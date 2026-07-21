from __future__ import annotations

import sys
import threading
import time

from multica_py._internal.concurrency import ProcessSemaphore
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig


def test_semaphore_limits_concurrency():
    """Prove semaphore blocks when limit is reached."""
    sem = ProcessSemaphore(max_processes=1)
    sem.acquire()
    blocked: list[str] = []

    def _acquire_and_record() -> None:
        sem.acquire()
        blocked.append("done")

    t = threading.Thread(target=_acquire_and_record)
    t.start()
    time.sleep(0.05)
    assert len(blocked) == 0, "Semaphore did not block"
    sem.release()
    t.join(timeout=1)
    assert len(blocked) == 1


def test_transport_releases_semaphore_on_success():
    """Prove transport releases semaphore after successful command."""
    sem = ProcessSemaphore(max_processes=1)
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config, semaphore=sem)
    transport.run_text(("-c", "print('ok')"))
    sem.acquire()
    sem.release()


def test_managed_process_wait_releases_semaphore() -> None:
    sem = ProcessSemaphore(max_processes=1)
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config, semaphore=sem)
    proc = transport.spawn(("-c", "print('ok')"))
    assert proc.wait() == 0
    sem.acquire()
    sem.release()
