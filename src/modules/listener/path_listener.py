"""
path_listener.py
(C) Lilith 2023
An adaptation of the functionality that py watchdog promised, but couldn't quite deliver
A threaded (via multiprocessing) watcher that rather than triggering events, just returns data via a queue
The use case for this is when the file you are watching is being changed asynchronously by another process,
and you are looking to grab the appended data as it is appended.

I.e. something like a `console.log` file that grows throughout the process lifetime of an application
"""
import datetime
import multiprocessing
import time
import os
import loguru

from multiprocessing import Queue, Process
from queue import Empty
from pathlib import Path
from typing import Callable
# from src.modules.tf2e.lobby import TF2Lobby, TF2Player
from src.modules.listener.status import TF2StatusBlob
from src.modules.rc.rcon_client import RCONListener
from src.modules.rc.FragClient import FragClient
from abc import ABC, abstractmethod
from enum import Enum


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
            # Need logging here to complain about failure to open the watched path
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

    def invoke_status(self) -> TF2StatusBlob | None:
        """
        For when the status command is to be invoked in the console, we aggressively munch all output until
        we have achieved a 'full munch' of the status invocation. Then we return a TF2StatusBlob
        object which contains all the munched data, as well as a list of the excess data it might have consumed
        during the munching.

        This tends to occur if other data gets interleaved with the `status` output.

        :return: A TF2StatusBlob instance (which contains the excess data)
        """
        _status = TF2StatusBlob()
        _time_started: datetime.datetime = datetime.datetime.now()
        _initial_data = self.get_update()
        _data_lines: list[str] = []

        while not _status.full_munch:
            if _initial_data is None:
                _initial_data = self.get_update()
                # If we pull None back from get_update() twice in a row, sleep for 50ms for every time
                # None is returned (i.e. give the watcher time to pull data and achieve the Queue lock)

            if _initial_data is None:
                time.sleep(0.05)
                _time = datetime.datetime.now() - _time_started
                if _time.seconds > 2:
                    return None

            if not _data_lines and _initial_data is not None:
                _data_lines = _initial_data.split("\n")
                _initial_data = None

            for line in _data_lines:
                if _status.munch(line):
                    break

            _data_lines = []

        return _status


class L2Events(Enum):
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    PLAYER_AUTO_BALANCED = "player_auto_balanced"
    PLAYER_AUTO_ASSIGNED = "player_auto_assigned"
    PLAYER_ASSIGNED = "player_assigned"
    PLAYER_SWITCHED = "player_switched_team"
    JOINED_GAME = "joined_game"
    LEFT_GAME = "left_game"


# class L2:
#     sentinel: Watchdog = None
#     event_handlers: dict[L2Events, Callable[[str, TF2Player | None, TF2Lobby | None], None]] = {
#         L2Events.PLAYER_JOINED: None,
#         L2Events.PLAYER_LEFT: None,
#         L2Events.PLAYER_AUTO_BALANCED: None,
#         L2Events.PLAYER_AUTO_ASSIGNED: None,
#         L2Events.PLAYER_ASSIGNED: None,
#         L2Events.PLAYER_SWITCHED: None,
#         L2Events.JOINED_GAME: None,
#         L2Events.LEFT_GAME: None,
#     }
#     lobby: TF2Lobby = None
#
#     def __init__(self, *args, **kwargs):
#         self.sentinel = Watchdog(*args, **kwargs)
#
#     def init_lobby_data(self, _lobby: TF2Lobby | None) -> None:
#         if self.lobby is not None:
#             raise AssertionError("Cannot init lobby data when lobby is not None. (Have you already called this before?)")
#         self.lobby = _lobby
#
#     def _raise_event(self, event: L2Events, event_str: str, player: TF2Player | None) -> None:
#         """
#         Doesn't raise an event if self.lobby is still none - need to initialise the lobby value first so it can
#         map player names appropriately.
#         :param event: The L2Event enum instance that was triggered by the incoming console stream
#         :param event_str: The console line that triggered the event instance
#         :param player: The player name mapped to the event, if applicable.
#         :return: None
#         """
#         if self.lobby is not None or (self.lobby is None and event == L2Events.JOINED_GAME):
#             _callable = self.event_handlers[event]
#             if _callable is None:
#                 return
#             else:
#                 _callable(event_str, player, self.lobby)
#
#     def register_handler(self, event: L2Events, _fn: Callable[[str, TF2Player | None, TF2Lobby | None], None]) -> None:
#         if type(event) is not L2Events:
#             raise TypeError(f"Event {event} is not of enum L2Events.")
#         if event not in self.event_handlers:
#             raise KeyError(f"Event {event} is not an allowed event to dispatch to.")
#         if self.event_handlers[event] is None:
#             self.event_handlers[event] = _fn
#         else:
#             raise ValueError(f"Event {event} already associated with a handler function "
#                              f"- use reassign_handler to override")
#
#     def reassign_handler(self, event: L2Events, _fn: Callable[[str, TF2Player | None, TF2Lobby | None], None]) -> None:
#         if type(event) is not L2Events:
#             raise TypeError(f"Event {event} is not of enum L2Events.")
#         if event not in self.event_handlers:
#             raise KeyError(f"Event {event} is not an allowed event to dispatch to.")
#         if self.event_handlers[event] is not None:
#             self.event_handlers[event] = _fn
#         else:
#             raise ValueError(f"Event {event} does not have an associated handler function "
#                              f"- use register_handler to set")


# Testing purposes only - not intended to function standalone
def main():
    _path = Path("D:\\Steam\\steamapps\\common\\Team Fortress 2\\tf\\console.log")
    _watcher = Watchdog(path=_path)
    _watcher.begin()
    # _rcon_handle = RCONListener(pword="lilith_is_hot")
    # _rcon_handle.spawn_client()
    # _watcher.get_update()
    # _resp = _rcon_handle.run("g15_dumpplayer")
    # _rcon_handle.
    # print("RESPONSE: ")
    # print(_resp)
    rcon_ip = "127.0.0.1"
    rcon_port = 27015
    rcon_pword = "lilith_is_hot"
    with FragClient(rcon_ip, rcon_port, passwd=rcon_pword) as h:
        resp = h.frag_run("g15_dumpplayer")
        print(resp)


if __name__ == "__main__":
    main()
