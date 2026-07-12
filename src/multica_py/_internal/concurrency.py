from __future__ import annotations

import threading


class ProcessSemaphore:
    def __init__(self, max_processes: int = 4) -> None:
        self._sem = threading.Semaphore(max_processes)
        self._max = max_processes

    @property
    def max_processes(self) -> int:
        return self._max

    def acquire(self) -> None:
        self._sem.acquire()

    def release(self) -> None:
        self._sem.release()

    def __enter__(self) -> ProcessSemaphore:
        self.acquire()
        return self

    def __exit__(self, *args: object) -> None:
        self.release()
