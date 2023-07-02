import datetime

from steam import Steam
from steamid_converter import Converter
from typing import Self, Any, Literal, Callable
from src.modules.rc.rcon_client import RCONListener, RCONHelper
from src.modules.caching.avatar_cache import AvCache
from src.modules.rc.FragClient import FragClient
from src.modules.g15parser.consumer import do_g15, G15DumpPlayer, Team
from src.modules.g15parser.helpers import get_player_stats_from_identifier, get_id3_from_iAccountID, PlayerDump
from src.modules.listener.path_listener import Watchdog
from src.modules.listener.status import TF2StatusBlob
from pathlib import Path
from threading import Thread, Lock
from abc import ABC, abstractmethod

import copy
import os
import re
import time
import loguru
import schedule


class PlayerAssociation(ABC):
    icon_str = NotImplemented
    label: str = None
    color: str = None  # american spelling to make linters happy >:3

    def __init__(self, label: str, color: str) -> None:
        self.label = label
        self.color = color

    def __str__(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def related_message(self) -> str:
        pass


class Friend(PlayerAssociation):
    icon_str = "friend"

    def __init__(self) -> None:
        super().__init__(label="Friend", color="green")

    def related_message(self) -> str:
        return "is a good friend :)"


class Trusted(PlayerAssociation):
    icon_str = "trusted"

    def __init__(self) -> None:
        super().__init__(label="Trusted", color="cyan")

    def related_message(self) -> str:
        return "is trusted"


class Neutral(PlayerAssociation):
    icon_str = "unknown"

    def __init__(self) -> None:
        super().__init__(label="Neutral", color="gray")

    def related_message(self) -> str:
        return "is unknown/unlabelled"


class Suspicious(PlayerAssociation):
    icon_str = "sus"

    def __init__(self) -> None:
        super().__init__(label="Suspicious", color="yellow")

    def related_message(self) -> str:
        return "is marked as suspicious"


class Cheater(PlayerAssociation):
    icon_str = "cheater"

    def __init__(self) -> None:
        super().__init__(label="Cheater", color="red")

    def related_message(self) -> str:
        return "is a confirmed cheater"


class Bot(PlayerAssociation):
    icon_str = "bot"

    def __init__(self) -> None:
        super().__init__(label="Bot", color="orange")

    def related_message(self) -> str:
        return "is a bot"


class Phobic(PlayerAssociation):
    icon_str = "unknown"  # TODO: Create an 'asshole' icon

    def __init__(self) -> None:
        super().__init__(label="Phobic", color="brown")

    def related_message(self) -> str:
        return "is LGBTQ-Phobic"


class DummyTF2Player:
    possible_associations: list[PlayerAssociation] = [
        Cheater(),
        Suspicious(),
        Bot(),
        Phobic(),
        Neutral(),
        Trusted(),
        Friend()
    ]

    steam: Steam = None
    steamID: str = "None"
    steamID3: str = "None"
    steamID64: str = "None"
    communityvisibilitystate: int = 0  # Example:3
    profilestate: int = 0  # Example: 1,
    personaname: str = "None"  # Example: "The12thChairman",
    profileurl: str = "None"  # Example: "https://steamcommunity.com/id/the12thchairman/",
    avatar: str = "None"  # Example: "https://avatars.akamai.steamstatic.com/427ef7d5f8ad7b21678f69bc8afc95786cf38fe6.jpg",
    avatarmedium: str = "None"  # Example: "https://avatars.akamai.steamstatic.com/427ef7d5f8ad7b21678f69bc8afc95786cf38fe6_medium.jpg",
    avatarfull: str = "None"  # Example: "https://avatars.akamai.steamstatic.com/427ef7d5f8ad7b21678f69bc8afc95786cf38fe6_full.jpg",
    avatarhash: str = "None"  # Example: "427ef7d5f8ad7b21678f69bc8afc95786cf38fe6",
    lastlogoff: int = 0  # Example: 1659923870,
    personastate: int = 0  # Example: 1,
    primaryclanid: str = "None"  # Example: "103582791429521408",
    timecreated: int = 0  # Example: 1570311509,
    personastateflags: int = 0  # Example: 0,
    loccountrycode: str = "None"  # Example: "US"

    ping: int = 0
    player_id: str = "None"
    game_time: int = 0
    player_state: str = "None"
    lobby_team: str = "None"  # Example: "TF_GC_TEAM_DEFENDERS"
    player_type: str = "None"  # Example: "MATCH_PLAYER"

    profile_init: bool = True
    association: PlayerAssociation = Neutral()
    game_team: Team = None
    pl_health: int = None
    pl_ammo: int = None
    ig_id: int = None
    pl_score: int = None
    pl_deaths: int = None

    dummy_id: int = None

    def __init__(self, dummy_id: int):
        self.dummy_id = dummy_id


class TF2Player:
    possible_associations: list[PlayerAssociation] = [
        Cheater(),
        Suspicious(),
        Bot(),
        Phobic(),
        Neutral(),
        Trusted(),
        Friend()
    ]

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

    ping: int = None
    player_id: str = None
    game_time: str = None
    player_state: str = None
    lobby_team: str = None  # Example: "TF_GC_TEAM_DEFENDERS"
    player_type: str = None  # Example: "MATCH_PLAYER"

    game_team: Team = None
    pl_health: int = None
    pl_ammo: int = None
    ig_id: int = None
    pl_score: int = None
    pl_deaths: int = None

    profile_init: bool = None
    association: PlayerAssociation = None
    dummy_id: int = 0  # real TF2Player instances will always have a 0 dummy id

    def __init__(self, steam_client: Steam, steam_id3: str):
        self.steamID = Converter.to_steamID(steam_id3)
        self.steamID3 = steam_id3
        self.steamID64 = Converter.to_steamID64(steam_id3)
        self.steam = steam_client
        self._lookup_profile()
        self.profile_init = True

        # TODO: Pull data from DB
        self.association = Neutral()

    def _lookup_profile(self):
        try:
            _response = self.steam.users.get_user_details(self.steamID64)['player']
            for class_field in _response.keys():
                if class_field == "steamid":
                    continue
                setattr(self, class_field, _response[class_field])

            if self.avatarhash is not None and self.avatarfull is not None:
                _db = AvCache(Path("NULL"))  # path should be initialised at this point because singleton.
                _db.cache_image(self.avatarhash, self.avatarfull)
        except IndexError:
            return

    # Example tf_lobby_debug line '  Member[0] [U:1:1067916592]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER'
    def set_lobby_status(self, tf_lobby_debug_player_str: str) -> None:
        self.lobby_team = tf_lobby_debug_player_str.split("team = ")[1].strip().split()[0]
        self.player_type = tf_lobby_debug_player_str.split("type = ")[1].strip().split()[0]

    # 0: full str, 1: userid, 2: Quote delimited username, 3: SteamID3, 4: time in server, 5: ping, 6: loss, 7: state
    def set_from_status(self, status_player_match_groups: tuple[Any, ...]) -> None:
        _groups = status_player_match_groups
        self.player_id = _groups[1]
        # self.personaname = _groups[2][1:len(self.personaname) - 1]
        self.steamID3 = _groups[3]
        self.steamID = Converter.to_steamID(self.steamID3)
        self.steamID64 = Converter.to_steamID64(self.steamID3)
        self.game_time = _groups[4]
        self.ping = _groups[5]
        self.player_state = _groups[6]

        if not self.profile_init:
            self._lookup_profile()

    def set_from_g15_player_dump(self, player_dump: PlayerDump) -> None:
        self.ping = player_dump.ping
        self.steamID3 = player_dump.steamid3
        self.steamID = Converter.to_steamID(self.steamID3)
        self.steamID64 = Converter.to_steamID64(self.steamID3)
        self.pl_score = player_dump.score
        self.pl_deaths = player_dump.deaths
        self.pl_ammo = player_dump.ammo
        self.pl_health = player_dump.health
        self.ig_id = player_dump.ig_id
        self.game_team = player_dump.team

        if not self.profile_init:
            self._lookup_profile()

    def set_association(self, association: PlayerAssociation) -> None:
        self.association = association

    def __str__(self) -> str:
        return self.personaname

    def __repr__(self) -> str:
        return self.__str__()


class TF2Lobby:
    lobby_id: str = None  # 'CTFLobbyShared: ID:00022b29776f570e  24 member(s), 0 pending',
    player_count: int = None  #
    pending_players: int = None
    players: list[TF2Player] = None
    exists: bool = None
    map: str = None
    server_id: str = None
    address: tuple[str, int] = None

    rcon: RCONListener = None
    rcon_conf: tuple[str, int, str] = None
    steam_: Steam = None
    listener: Watchdog = None

    last_update: datetime.datetime = None
    update_order: list[Callable] = None
    update_location: int = None

    def __init__(self, players: list[TF2Player], lobby_data: str) -> None:

        self.lobby_lock = Lock()
        self.players = players
        self.lobby_id = lobby_data.split("ID:")[1].split()[0]
        self.player_count = int(lobby_data.split(self.lobby_id)[1].strip().split()[0])
        self.pending_players = int(lobby_data.split(",")[1].strip().split()[0])
        self.exists = self.lobby_id != "0000000000000000"
        self.map = "Unknown"
        self.server_id = "Unknown"
        self.address = ("Unknown", 0)
        self.last_update = datetime.datetime.now()

        self.update_order = [
            self.update_from_status,
            self.update_from_g15,
            self.update_from_g15,
            self.update_from_g15,
            self.update_from_g15,
        ]
        self.update_location = 0

    def get_player_by_nick(self, nickname: str) -> TF2Player | None:
        with self.lobby_lock:
            for _pl in self.players:
                if _pl.personaname == nickname:
                    return _pl

        return None

    def set_iclients(self, rcon_client, steam_client) -> None:
        self.rcon = rcon_client
        self.rcon_conf = (self.rcon.rcon_ip, self.rcon.rcon_port, self.rcon.rcon_pword)
        self.steam_ = steam_client

    def connect_listener(self, listener: Watchdog) -> None:
        self.listener = listener

    def update(self) -> bool:
        """
        Update lobby and player data using output from `tf_lobby_debug`, but this is not optimal as this _only_ works
        in official match-made servers. This also gives somewhat useful team data, but no relevant in game player data
        like scores, ping, game time, etc...

        :return: True if any modifications were made
        """
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

        # self.last_update = datetime.datetime.now()
        return changes_made

    def update_from_g15(self):
        """ Update the player entries from a `g15_dumpplayer` command invocation. """
        try:
            _g15_dump = do_g15(self.rcon_conf)
        except ValueError:
            return
        except IndexError:
            return
        _to_remove = []
        _found = []

        with self.lobby_lock:
            for _pl in self.players:
                try:
                    _pd = get_player_stats_from_identifier(_g15_dump, sid3=_pl.steamID3)
                    _pl.set_from_g15_player_dump(_pd)
                    _found.append(_pl.steamID3)
                except ValueError:
                    _to_remove.append(_pl)

        with self.lobby_lock:
            for aid in _g15_dump.get_local_player_resource_data().m_iAccountID:
                _id3 = get_id3_from_iAccountID(aid)
                if _id3 not in _found:
                    _pl = TF2Player(self.steam_, _id3)
                    _pl.set_from_g15_player_dump(get_player_stats_from_identifier(_g15_dump, sid3=_id3))
                    self.players.append(_pl)

        with self.lobby_lock:
            for _rpl in _to_remove:
                self.players.remove(_rpl)

    def update_from_status(self):
        """
        Update player and lobby data from a status command invocation.
        This is the only way to get the `game_time` values populated per player.
        """
        self.listener.get_update()
        RCONHelper.invoke_status(self.rcon)
        status: TF2StatusBlob | None = self.listener.invoke_status()

        if status is None:
            if self.exists:
                with self.lobby_lock:
                    self.players = []
                    self.lobby_id = "0000000000000000"
                    self.player_count = 0
                    self.pending_players = 0
                    self.exists = False
                    loguru.logger.info(f"No longer in valid lobby.")
            loguru.logger.info("No lobby. ")
            return
        self.listener.changes.put("\n".join(status.excess_junk), block=True, timeout=None)
        _existing_sid3 = [(x.steamID3, x) for x in self.players]

        for player_match in status.players:
            _found_player: bool = False
            _groups = player_match.groups()

            _sid3 = _groups[3].strip()
            for _exist_sid3, _player in _existing_sid3:
                if _sid3 == _exist_sid3:
                    _player.set_from_status(_groups)
                    _found_player = True

            _to_add = []
            if not _found_player:
                _new_player = TF2Player(self.steam_, _sid3)
                _new_player.set_from_status(_groups)
                with self.lobby_lock:
                    self.players.append(_new_player)

        with self.lobby_lock:
            self.map = status.status_map.strip().split()[0]
            self.address = (status.status_udp.split(":")[0], int(status.status_udp.split(":")[1]))
            self.server_id = status.status_sid
            self.player_count = status.num_players

        # self.last_update = datetime.datetime.now()

    def update_sequenced(self) -> None:
        _update_method = self.update_order[self.update_location]
        self.update_location += 1
        self.update_location %= len(self.update_order)
        _update_method()
        self.last_update = datetime.datetime.now()

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
        self.rcon_conf = (self.rcon.rcon_ip, self.rcon.rcon_port, self.rcon.rcon_pword)
        self.steam = steam_iclient
        self.lobby = TF2Lobby.spawn_from_tf_lobby_debug(RCONHelper.get_lobby_data(self.rcon))
        self.lobby.set_iclients(self.rcon, self.steam)
        self.schedule_job = schedule.every(7).seconds.do(job_func=self.lobby.update_sequenced)
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
