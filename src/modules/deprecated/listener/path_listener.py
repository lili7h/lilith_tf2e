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
import re
import time
import os
import loguru

from multiprocessing import Queue, Process
from queue import Empty
from pathlib import Path
from src.modules.deprecated.listener.status import TF2StatusBlob
from src.modules.backend.rc import FragClient
from enum import Enum
from typing import Callable
from src.modules.backend.lobby import TF2Lobby, TF2Player


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
            with open(str(watching), read_mode, encoding='utf16', errors='replace') as h:
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


PREFIX_LEN: int = 10
HST_REGEX: str = r"^hostname:\s*(.+)$"
VER_REGEX: str = r"^version\s*:\s*(.+)$"
UDP_REGEX: str = r"^udp/ip\s*:\s*([^:]+):*(.*)$"
SID_REGEX: str = r"^steamid\s*:\s*(\[.+\])\s+(\(.+\))$"
ACC_REGEX: str = r"^account\s*:\s*(.*)$"
MAP_REGEX: str = r"^map\s*:\s*(\S*)(.*)$"
TAG_REGEX: str = r"^tags\s*:\s*(.*)$"
PLS_REGEX: str = r"^players\s*:\s*(\d+)\s*humans,\s*(\d+)\s*bots\s*\((\d+)\s*max\)$"
EDS_PREFIX: str = r"^edicts\s*:\s*(\d+)\s*used\s*of\s*(\d+)\s*max$"
# No groups
# list seperator example: # userid name                uniqueid            connected ping loss state
PLAYER_LIST_SEPARATOR_REGEX: str = r"^#\s+userid\s+name\s+uniqueid\s+connected\s+ping\s+loss\s+state$"
# Groups ordering:
# 0: full str, 1: userid, 2: Quote delimited username, 3: SteamID3, 4: time in server, 5: ping, 6: loss, 7: state
PLAYER_LIST_LINE_REGEX: str = \
    r'^(#\s+(\d{2,4})\s+(".+")\s+(\[U:\d:\d+\])\s+(\d?:?\d{2}:\d{2})\s+(\d{1,3})\s+(\d{1,3})\s+(\S+))$'


def track_console_against_lobby(
        lobby: TF2Lobby,
        tfpath: Path,
        *,
        full_start: bool = False
):
    """
    Multithread this with threading.
    
    :param tfpath:
    :param full_start:
    :param lobby:
    :return: 
    """
    _listener = Watchdog(path=tfpath, full_start=full_start)
    _listener.begin()
    regexes = {
        HST_REGEX: "hostname",
        VER_REGEX: "none",
        UDP_REGEX: "gameIp",
        SID_REGEX: "none",
        ACC_REGEX: "none",
        MAP_REGEX: "gameMap",
        TAG_REGEX: "none",
        PLS_REGEX: ["int->numPlayers", "none", "int->maxPlayers"],
        EDS_PREFIX: "none",
        PLAYER_LIST_SEPARATOR_REGEX: "none",
        PLAYER_LIST_LINE_REGEX: "__PLAYER__",
    }
    while True:
        _data = _listener.get_update()
        _lines = _data.split("\n")
        _cleaned = [x.strip() for x in _lines]
        for _line in _cleaned:
            for _k in regexes:
                if regexes[_k] == "none":
                    continue

                _match = re.search(_k, _line)
                if not _match:
                    continue

                if type(regexes[_k]) is list:
                    _groups = _match.groups()
                    for idx, grp in enumerate(_groups):
                        _attr = regexes[_k][idx]
                        if _attr == "none":
                            continue
                        _caster: Callable = str
                        if "int->" in _attr:
                            _caster = int
                            _attr = _attr.replace("int->", "")
                        elif "float->" in _attr:
                            _caster = float
                            _attr = _attr.replace("float->", "")

                        setattr(lobby, _attr, _caster(grp))
                else:

                    _attr = regexes[_k]
                    if _attr == "none":
                        continue

                    if _attr == "__PLAYER__":
                        pass
                    # TODO: finish this

                    _groups = _match.groups()
                    _caster: Callable = str
                    if "int->" in _attr:
                        _caster = int
                        _attr = _attr.replace("int->", "")
                    elif "float->" in _attr:
                        _caster = float
                        _attr = _attr.replace("float->", "")
                    setattr(lobby, _attr, _caster(_groups[0]))



