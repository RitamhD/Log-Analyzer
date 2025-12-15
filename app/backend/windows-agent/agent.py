import yaml
import queue
import threading
import time
from utils import setup_logger, get_hostname, gen_id
from win_collector import WindowsEventCollector
from ws_client import WebSocketClient
from batch_worker import BatchWorker

def load_config(path="config.yaml"):
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)
    if not cfg.get("agent"):
        cfg["agent"] = {}
    if not cfg["agent"].get("hostname"):
        cfg["agent"]["hostname"] = get_hostname()
    return cfg

def main():
    cfg = load_config("config.yaml")
    logger = setup_logger("win-agent")
    logger.info("Starting console agent")

    # main queue for raw events from collector
    event_queue = queue.Queue()

    # Collector (Windows Event Viewer)
    channels = cfg.get("collector", {}).get("channels", ["System","Application"])
    collector = WindowsEventCollector(channels=channels, out_queue=event_queue, cfg=cfg, logger_=logger)
    collector.start()

    # WebSocket client for live streaming
    ws_url = cfg.get("transport", {}).get("websocket_url")
    auth_token = cfg.get("security", {}).get("auth_token")
    ws_client = WebSocketClient(ws_url, logger, auth_token=auth_token, on_message=None, 
                            reconnect_backoff=cfg.get("transport", {}).get("ws_reconnect_backoff", 2))
    ws_client.start()

    # We will duplicate events: forwarder takes events from collector (event_queue),
    # sends one copy to ws_client, and puts another copy into batch_queue.
    batch_queue = queue.Queue()

    def forwarder():
        while True:
            item = event_queue.get()
            # augment agent fields
            item["agent_id"] = cfg.get("agent", {}).get("agent_id", gen_id())
            item["hostname"] = cfg.get("agent", {}).get("hostname")
            # send live via websocket (best-effort)
            try:
                ws_client.send_now(item)
            except Exception:
                logger.exception("Failed to send live event over WS")
            # enqueue for batch (duplicate)
            batch_queue.put(item)

    forwarder_thread = threading.Thread(target=forwarder, daemon=True)
    forwarder_thread.start()

    # Start batch worker using batch_queue
    analyze_url = cfg.get("transport", {}).get("analyze_url")
    batch_interval = cfg.get("batch", {}).get("interval_seconds", 5)
    batch_worker = BatchWorker(in_queue=batch_queue, analyze_url=analyze_url, batch_interval=batch_interval,
                               auth_token=auth_token, logger=logger, verify_tls=cfg.get("security", {}).get("verify_tls", True))
    batch_worker.start()

    logger.info("Agent running. Press Ctrl+C to stop. (Run as Administrator to read Security channel)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down")
        collector.stop()
        ws_client.stop()
        batch_worker.stop()

if __name__ == "__main__":
    main()
