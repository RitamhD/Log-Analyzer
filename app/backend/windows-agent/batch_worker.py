import threading
import time
import httpx
from utils import now_iso

class BatchWorker:
    """
    Drains a queue every batch_interval seconds and sends collected events to analyze_url.
    """
    def __init__(self, in_queue, analyze_url, batch_interval, auth_token, logger, verify_tls=True):
        self.in_queue = in_queue
        self.analyze_url = analyze_url
        self.batch_interval = float(batch_interval)
        self.auth_token = auth_token
        self.logger = logger
        self.verify_tls = verify_tls
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _gather_batch(self):
        batch = []
        try:
            while True:
                item = self.in_queue.get_nowait()
                batch.append(item)
        except Exception:
            # queue.Empty or other; simply return gathered batch
            pass
        return batch

    def _loop(self):
        self.logger.info("Batch worker started; interval %ss", self.batch_interval)
        while not self._stop.is_set():
            time.sleep(self.batch_interval)
            batch = self._gather_batch()
            if not batch:
                continue
            payload = {"agent_id": batch[0].get("agent_id"), "hostname": batch[0].get("hostname"), "batch_ts": now_iso(), "events": batch}
            headers = {"Content-Type": "application/json"}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"

            try:
                with httpx.Client(verify=self.verify_tls, timeout=30.0) as client:
                    r = client.post(self.analyze_url, json=payload, headers=headers)
                    if r.status_code >= 400:
                        self.logger.warning("Analyze endpoint returned %s: %s", r.status_code, r.text)
                    else:
                        try:
                            resp = r.json()
                            self.logger.info("Batch analyzed; count=%s resp=%s", len(batch), resp)
                        except Exception:
                            self.logger.info("Batch sent; count=%s; no json resp", len(batch))
            except Exception:
                self.logger.exception("Error sending batch to analyze endpoint")
