import threading
import time

import psutil


class PeakMemory:

    def __init__(self, interval=0.1):
        self.interval = interval
        self.peak_bytes = 0
        self.timeline = []  # (seconds, MB)
        self._stop = threading.Event()
        self._proc = psutil.Process()

    def _rss(self):
        total = self._proc.memory_info().rss
        for child in self._proc.children(recursive=True):
            try:
                total += child.memory_info().rss
            except psutil.Error:
                pass
        return total

    def _run(self):
        t0 = time.perf_counter()
        while not self._stop.is_set():
            rss = self._rss()
            self.peak_bytes = max(self.peak_bytes, rss)
            self.timeline.append((time.perf_counter() - t0, rss / 1024**2))
            time.sleep(self.interval)

    def __enter__(self):
        self.start_rss = self._rss()
        self.peak_bytes = self.start_rss
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join()
        self.peak_bytes = max(self.peak_bytes, self._rss())

    @property
    def peak_mb(self):
        return self.peak_bytes / 1024**2


def system_ram_gb():
    return psutil.virtual_memory().total / 1024**3
