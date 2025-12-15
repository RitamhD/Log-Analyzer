import logging
import socket
import uuid
from datetime import datetime

def setup_logger(name="win-agent", level=logging.INFO):
    logger = logging.getLogger(name)
    if not logger.handlers:
        ch = logging.StreamHandler()
        fmt = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    logger.setLevel(level)
    return logger

def now_iso():
    return datetime.now().isoformat() + "Z"

def gen_id():
    return str(uuid.uuid4())

def get_hostname():
    try:
        return socket.gethostname()
    except Exception:
        return "unknown-host"
