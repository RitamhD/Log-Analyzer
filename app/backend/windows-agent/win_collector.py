import time
import threading
import queue
from utils import now_iso, gen_id, get_hostname

logger = None

try:
    import win32evtlog
    WIN32EVT_AVAILABLE = True
except Exception:
    WIN32EVT_AVAILABLE = False

class WindowsEventCollector:
    """
    Polling-based Windows Event Viewer collector.
    - channels: list of channel names (System, Application, Security, ...)
    - out_queue: queue.Queue where normalized events are placed
    - cfg: config dict (to read poll interval)
    - logger_: logger instance
    """
    def __init__(self, channels, out_queue: queue.Queue, cfg: dict, logger_):
        global logger
        logger = logger_
        self.channels = channels
        self.out_queue = out_queue
        self.poll_interval = float(cfg.get("collector", {}).get("poll_interval_seconds", 1.0))
        self._stop = threading.Event()
        self._threads = []
        # Track last record number per channel to avoid duplicates
        self.last_record = {ch: 0 for ch in channels}

    def start(self):
        # Single poll thread
        t = threading.Thread(target=self._poll_loop, daemon=True)
        t.start()
        self._threads.append(t)
        logger.info("WindowsEventCollector started (polling) - channels: %s", ", ".join(self.channels))

    def stop(self):
        self._stop.set()
        for t in self._threads:
            t.join(timeout=1)

    def _poll_loop(self):
        logger.info("Starting polling loop; poll interval %.3fs", self.poll_interval)
        server = "localhost"

        while not self._stop.is_set():
            try:
                for ch in self.channels:
                    try:
                        hand = win32evtlog.OpenEventLog(server, ch)

                        total = win32evtlog.GetNumberOfEventLogRecords(hand)

                        # Initialize pointer (skip history)
                        if self.last_record[ch] == 0:
                            self.last_record[ch] = total
                            continue

                        # If no new logs
                        if total <= self.last_record[ch]:
                            continue

                        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

                        events = win32evtlog.ReadEventLog(hand, flags, 0)
                        if not events:
                            continue

                        new_events = []
                        for ev in events:
                            rec_no = ev.RecordNumber
                            if rec_no <= self.last_record[ch]:
                                break  # we've reached old logs

                            new_events.append(ev)

                        # Reverse to chronological order
                        new_events.reverse()

                        for ev in new_events:
                            msg = ""
                            if getattr(ev, "StringInserts", None):
                                msg = "\n".join([str(x) for x in ev.StringInserts if x])
                            else:
                                msg = str(ev)

                            item = {
                                "internal_id": gen_id(),
                                "agent_id": "win-agent-01",
                                "hostname": get_hostname(),
                                "channel": ch,
                                "record_number": ev.RecordNumber,
                                "event_id": getattr(ev, "EventID", None),
                                "category": getattr(ev, "EventCategory", None),
                                "source_name": getattr(ev, "SourceName", None),
                                "computer": getattr(ev, "ComputerName", None),
                                "time_generated": ev.TimeGenerated.Format() if ev.TimeGenerated else now_iso(),
                                "message": msg,
                                "ingest_ts": now_iso()
                            }
                            self.out_queue.put(item)
                        self.last_record[ch] = total

                    except Exception:
                        logger.exception("Error reading channel %s", ch)

                time.sleep(self.poll_interval)

            except Exception:
                logger.exception("Top-level poll loop error")
                time.sleep(self.poll_interval)
