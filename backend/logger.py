# backend/logger.py
from PyQt5.QtCore import QObject, pyqtSignal
import threading
import datetime
import os

class Logger(QObject):
    """
    Thread-safe singleton logger that emits a Qt signal on new log lines.
    Use Logger.instance().log(...) from anywhere (threadsafe).
    """
    new_log = pyqtSignal(str)

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        super().__init__()
        self._lines = []
        self._lines_lock = threading.Lock()

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = Logger()
            return cls._instance

    def _timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log(self, message: str, level: str = "INFO"):
        """
        Append a message with timestamp and emit signal.
        level: INFO, WARN, ERROR, DEBUG
        """
        ts = self._timestamp()
        line = f"[{ts}] [{level}] {message}"
        with self._lines_lock:
            self._lines.append(line)
        # emit signal for UI (Qt signal; safe to emit from main thread; if called from other threads it still works)
        try:
            self.new_log.emit(line)
        except Exception:
            # signal may not be connected — that's fine
            pass

    def get_all(self):
        with self._lines_lock:
            return list(self._lines)

    def clear(self):
        with self._lines_lock:
            self._lines.clear()
        # inform UI
        try:
            self.new_log.emit("[LOGGER] CLEARED")
        except Exception:
            pass

    def save_to_file(self, path: str):
        with self._lines_lock:
            data = "\n".join(self._lines)
        folder = os.path.dirname(path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(data)
        self.log(f"Saved logs to {path}", level="INFO")
