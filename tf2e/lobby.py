import threading

from steam import Steam
from steamid_converter import Converter
from typing import Self
from rc.rcon_client import RCONListener, RCONHelper
from threading import Thread, Lock

import os
import re
import time
import loguru
import schedule


class TF2Player:
    steam: Steam = None
    steamID: str = None
    steamID3: str = None
    steamID64: str = None
    communityvisibilitystate: int = None  # Example:3
    profilestate: int = None  # Example: 1,
    personaname: str = None  # Example: "The12thChairman",
    profileurl: str = None  # Example: "https://steamcommunity.com/id/the12thchairman/",
    avatar: str = None  # Example: "https://avatars.akamai.steamstatic.com/427ef7d5f8ad7b21678f69bc8afc95786cf38fe6.jpg",
    avatarmedium: str = None  # Example: "https://avatars.akamai.steamstatic.com/427ef7d5f8ad7b21678f69bc8afc95786cf38fe6_medium.jpg",
    avatarfull: str = None  # Example: "https://avatars.akamai.steamstatic.com/427ef7d5f8ad7b21678f69bc8afc95786cf38fe6_full.jpg",
    avatarhash: str = None  # Example: "427ef7d5f8ad7b21678f69bc8afc95786cf38fe6",
    lastlogoff: int = None  # Example: 1659923870,
    personastate: int = None  # Example: 1,
    primaryclanid: str = None  # Example: "103582791429521408",
    timecreated: int = None  # Example: 1570311509,
    personastateflags: int = None  # Example: 0,
    loccountrycode: str = None  # Example: "US"

    lobby_team: str = None  # Example: "TF_GC_TEAM_DEFENDERS"
    player_type: str = None  # Example: "MATCH_PLAYER"

    def __init__(self, steam_client: Steam, steam_id3: str):
        self.steamID = Converter.to_steamID(steam_id3)
        self.steamID3 = steam_id3
        self.steamID64 = Converter.to_steamID64(steam_id3)
        self.steam = steam_client
        self._lookup_profile()

    def _lookup_profile(self):
        _response = self.steam.users.get_user_details(self.steamID64)['player']
        for class_field in _response.keys():
            if class_field == "steamid":
                continue
            setattr(self, class_field, _response[class_field])

    # Example tf_lobby_debug line '  Member[0] [U:1:1067916592]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER'
    def set_lobby_status(self, tf_lobby_debug_player_str: str) -> None:
        self.lobby_team = tf_lobby_debug_player_str.split("team = ")[1].strip().split()[0]
        self.player_type = tf_lobby_debug_player_str.split("type = ")[1].strip().split()[0]

    def __str__(self) -> str:
        return self.personaname

    def __repr__(self) -> str:
        return self.__str__()


class TF2Lobby:
    lobby_id: str = None         # 'CTFLobbyShared: ID:00022b29776f570e  24 member(s), 0 pending',
    player_count: int = None     #
    pending_players: int = None
    players: list[TF2Player] = None
    exists: bool = None

    def __init__(self, players: list[TF2Player], lobby_data: str) -> None:
        self.lobby_lock = Lock()
        self.players = players
        self.lobby_id = lobby_data.split("ID:")[1].split()[0]
        self.player_count = int(lobby_data.split(self.lobby_id)[1].strip().split()[0])
        self.pending_players = int(lobby_data.split(",")[1].strip().split()[0])
        self.exists = self.lobby_id != "0000000000000000"
        self.rcon = None
        self.steam_ = None

    def set_iclients(self, rcon_client, steam_client) -> None:
        self.rcon = rcon_client
        self.steam_ = steam_client

    def update(self) -> bool:
        data = RCONHelper.get_lobby_data(self.rcon)
        if data.strip() == "Failed to find lobby shared object":
            # Went from existing valid lobby to non-existing invalid lobby
            # e.g. player quit the game
            if self.exists:
                with self.lobby_lock:
                    self.players = []
                    self.lobby_id = "0000000000000000"
                    self.player_count = 0
                    self.pending_players = 0
                    self.exists = False
                    loguru.logger.info(f"No longer in valid lobby.")
                return True
            else:
                loguru.logger.info(f"Not in valid lobby.")
                return False
        # flag to track if modifications have been made for the return value of this function
        changes_made: bool = False

        # Regex search the tf_lobby_debug string for SteamID3's
        found_player_ids = []
        data_list = data.split("\n")
        sid_re_match = r"(\[U:\d:\d+\])"
        for line in data_list[1:]:
            _search = re.search(sid_re_match, line)
            if _search is None:
                continue
            sid = _search.group()
            found_player_ids.append(sid)
            # update existing players lobby status every time we read the tf_lobby_debug str
            with self.lobby_lock:
                for _pl in self.players:
                    if _pl.steamID3 == sid:
                        _pl.set_lobby_status(line)

        # Find all players in the current self.players list that are not in the tf_lobby_debug string
        to_remove = []
        for _player in self.players:
            if _player.steamID3 not in found_player_ids:
                to_remove.append(_player)

        # Remove all players previously found from self.players
        for rem in to_remove:
            with self.lobby_lock:
                self.players.remove(rem)
            changes_made = True

        # Find any players in the tf_lobby_debug string not in the self.players list, and add them.
        for sid in found_player_ids:
            if not any(map(lambda x: x.steamID3 == sid, self.players)):
                with self.lobby_lock:
                    self.players.append(TF2Player(self.steam_, steam_id3=str(sid)))
                changes_made = True

        # update lobby metadata from the first line of tf_lobby_debug output
        lobby_data = data_list[0]
        with self.lobby_lock:
            try:
                self.lobby_id = lobby_data.split("ID:")[1].split()[0]
                self.player_count = int(lobby_data.split(self.lobby_id)[1].strip().split()[0])
                self.pending_players = int(lobby_data.split(",")[1].strip().split()[0])
                self.exists = self.lobby_id != "0000000000000000"
            except IndexError:
                loguru.logger.warning(f"Invalid lobby data block received.")
                pass

        if changes_made:
            loguru.logger.info(f"Updated lobby with new data.")
        else:
            loguru.logger.info(f"Lobby status unchanged.")
        return changes_made

    @classmethod
    def spawn_from_tf_lobby_debug(cls, tf_lobby_debug_str: str, _steam: Steam | None = None) -> Self:
        if tf_lobby_debug_str.strip() == "Failed to find lobby shared object":
            return TF2Lobby(players=[], lobby_data='CTFLobbyShared: ID:0000000000000000  0 member(s), 0 pending')

        tf_lobby_debug_str_list = tf_lobby_debug_str.split("\n")
        _steam = Steam(os.environ["STEAM_WEB_API_KEY"]) if _steam is None else _steam
        sid_re_match = r"(\[U:\d:\d+\])"
        lobby_players = []
        for tf_lobby_debug_player in tf_lobby_debug_str_list[1:]:
            _search = re.search(sid_re_match, tf_lobby_debug_player)
            if _search is None:
                continue
            sid = _search.group()

            _player = TF2Player(_steam, steam_id3=str(sid))
            _player.set_lobby_status(tf_lobby_debug_player)
            lobby_players.append(_player)

        return TF2Lobby(lobby_players, tf_lobby_debug_str_list[0])


class LobbyWatching:

    def __init__(self, rcon_iclient: RCONListener, steam_iclient: Steam) -> None:
        self.rcon = rcon_iclient
        self.steam = steam_iclient
        self.lobby = TF2Lobby.spawn_from_tf_lobby_debug(RCONHelper.get_lobby_data(self.rcon))
        self.lobby.set_iclients(self.rcon, self.steam)
        self.schedule_job = schedule.every(5).seconds.do(job_func=self.lobby.update)
        self._run_scheduler = True
        self.schedule_proc = Thread(
            target=self._manage_scheduler,
            args=(),
            daemon=True,
            name="LobbyWatching-update-scheduler"
        )
        self.schedule_proc.start()

    def _manage_scheduler(self) -> None:
        while self._run_scheduler:
            schedule.run_pending()
            time.sleep(1)

    def _end_scheduler(self):
        self._run_scheduler = False
        schedule.cancel_job(self.schedule_job)
        self.schedule_proc.join()

    def kill_watcher(self):
        self._end_scheduler()
