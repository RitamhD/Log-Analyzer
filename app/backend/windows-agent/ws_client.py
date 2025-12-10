import asyncio
import threading
import json
import time
import websockets
from queue import SimpleQueue

class WebSocketClient:
    def __init__(self, url, logger, auth_token=None, on_message=None, reconnect_backoff=2):
        self.base_url = url
        self.auth_token = auth_token
        self.logger = logger
        self.on_message = on_message
        self.reconnect_backoff = reconnect_backoff

        self._send_queue = SimpleQueue()
        self._stop = threading.Event()

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def stop(self):
        self._stop.set()

    def send_now(self, data: dict):
        try:
            self._send_queue.put(data)
        except:
            self.logger.exception("Failed to enqueue WebSocket data")

    def _run(self):
        asyncio.run(self._async_loop())

    async def _async_loop(self):
        backoff = self.reconnect_backoff

        while not self._stop.is_set():
            try:
                url = self.base_url
                if self.auth_token:
                    url += f"?token={self.auth_token}"

                async with websockets.connect(url) as ws:
                    self.logger.info("WebSocket connected to %s", url)
                    backoff = self.reconnect_backoff

                    while not self._stop.is_set():
                        # Send queued messages if present
                        if not self._send_queue.empty():
                            item = self._send_queue.get()
                            try:
                                await ws.send(json.dumps(item))
                            except:
                                self.logger.exception("WS send failed")
                                break

                        # Receive incoming messages if any
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=0.1)
                            if self.on_message:
                                self.on_message(msg)
                        except asyncio.TimeoutError:
                            pass
                        except Exception:
                            self.logger.exception("WS recv error")
                            break

            except Exception as e:
                self.logger.warning("WS connection error: %s. reconnecting in %s s", e, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
