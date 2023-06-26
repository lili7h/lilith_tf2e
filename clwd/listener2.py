"""
listener2.py
(C) Lilith 2023
An adaptation of the functionality that py watchdog promised, but couldn't quite deliver
A threaded (via multiprocessing) watcher that rather than triggering events, just returns data via a queue
The use case for this is when the file you are watching is being changed asynchronously by another process,
and you are looking to grab the appended data as it is appended.

I.e. something like a `console.log` file that grows throughout the process lifetime of an application
"""
import multiprocessing
import time
import os
import loguru

from multiprocessing import Queue, Process
from queue import Empty
from pathlib import Path


def threaded_watcher(
        changes: Queue,
        watching: Path,
        full_start: bool,
        read_mode: str = "r",
        polling_rate: int = 10,
) -> None:
    """
    🚫 no access 🚫
    threaded_watcher

    :param changes: the managed multiprocessing Queue to output changes into to be synced with parent threads
    :param watching: the path to watch
    :param full_start: if true, treat the file as completely unseen and push whatever contents exist in the file into
                       the queue immediately. when false we initialise by setting the cursor to the current filesize.
    :param read_mode: the 'mode' passed to `open()` to open the watched file as. 'r' default for files where you expect
                      utf8 data, or for example, 'rb' where you expect raw binary data.
    :param polling_rate: the (ideal) polling rate (in Hz) of the file being watched. I.e. polling_rate = 10 will sleep
                         for 0.1 seconds between each polling cycle. This does not account for time taken to perform the
                         actual polling.
    :param logger: a multiprocessing Queue managed by the LilithLogger class from the master process. Used for logging.
    :return: None
    """
    # _nm --> private no mangle
    _nm_stat: os.stat_result = os.stat(str(watching))
    _nm_cursor: int = 0 if full_start else _nm_stat.st_size
    _nm_parent_check: int = 0
    _PARENT_CHECK_FREQ: int = 5
    while True:
        time.sleep(1.0 / polling_rate)
        # liveness check (check if parent is alive every
        # _PARENT_CHECK_FREQ loops, i.e. every _PARENT_CHECK_FREQ/10 seconds)
        if _nm_parent_check == (_PARENT_CHECK_FREQ - 1):
            if not multiprocessing.parent_process().is_alive():
                break
        else:
            _nm_parent_check += 1
            _nm_parent_check %= _PARENT_CHECK_FREQ

        # file metadata check
        _inst_stat: os.stat_result = os.stat(str(watching))
        if _inst_stat == _nm_stat:
            continue

        _nm_stat = _inst_stat

        # Bounds check the cursor
        if _nm_cursor > _nm_stat.st_size:
            # TODO: Because this is a child process, nothing captures this logging output,
            #       use a process safe logger (i.e. implement LilithLogger)
            _nm_cursor = 0

        # Try and read changes
        # Since we are opening a file in a child process, nothing can have a read lock
        # on the given fd, otherwise this fails. Since we are reading, we do not impact
        # the external process from achieving a write-lock on the file.
        try:
            with open(str(watching), read_mode, encoding='utf8') as h:
                h.seek(_nm_cursor)
                _inst_new_changes = h.read()
                _nm_cursor = h.tell()

            # Append read changes to managed queue
            if _inst_new_changes:
                changes.put(_inst_new_changes, block=True, timeout=None)

        except OSError as e:
            continue


class Watchdog:
    _watchdog: Process = None
    changes: Queue = None
    watching: Path = None
    fn: str = None
    wd_logger: Queue = None

    def __init__(self, path: Path, full_start: bool = False) -> None:
        self.watching: Path = path
        self.fn: str = path.name
        self.changes = Queue()
        self._watchdog = Process(target=threaded_watcher, args=(self.changes, self.watching, full_start), daemon=True)

    def begin(self) -> None:
        loguru.logger.info("starting path watchdog...")
        self._watchdog.start()

    def end(self) -> None:
        loguru.logger.info("killing path watchdog...")
        self._watchdog.kill()

    def get_update(self) -> None | str:
        try:
            return self.changes.get_nowait()
        except Empty:
            return None


# Testing purposes only - not intended to function standalone
def main():
    _path = Path("D:\\Steam\\steamapps\\common\\Team Fortress 2\\tf\\console.log")
    _watcher = Watchdog(path=_path)
    _watcher.begin()
    while True:
        time.sleep(0.1)
        # Todo: batch updates better - perhaps by dumping whole lists of strings at once, rather than by line?
        _data = _watcher.get_update()
        if _data is not None:
            for line in _data.split("\n"):
                if not line:
                    continue
                loguru.logger.success(f"CLWD: {line}")


if __name__ == "__main__":
    main()
