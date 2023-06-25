from steam import Steam
from dotenv import load_dotenv
from steamid_converter import Converter
from typing import Self
from rcon.source import Client

import os
import re


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

    # Example tf_lobby_debug_player_str: '  Member[0] [U:1:1067916592]  team = TF_GC_TEAM_DEFENDERS  type = MATCH_PLAYER'
    def set_lobby_status(self, tf_lobby_debug_player_str: str) -> None:
        self.lobby_team = tf_lobby_debug_player_str.split("team = ")[1].strip().split()[0]
        self.player_type = tf_lobby_debug_player_str.split("type = ")[1].strip().split()[0]


class TF2Lobby:
    lobby_id: str = None         # 'CTFLobbyShared: ID:00022b29776f570e  24 member(s), 0 pending',
    player_count: int = None     #
    pending_players: int = None
    players: list[TF2Player]

    def __init__(self, players: list[TF2Player], lobby_data: str) -> None:
        self.players = players
        self.lobby_id = lobby_data.split("ID:")[1].split()[0]
        self.player_count = int(lobby_data.split(self.lobby_id)[1].strip().split()[0])
        self.pending_players = int(lobby_data.split(",")[1].strip().split()[0])

    @classmethod
    def spawn_from_tf_lobby_debug(cls, tf_lobby_debug_str_list: list[str], _steam: Steam | None = None) -> Self:
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


def test(_steam: Steam) -> list[str]:
    with Client('127.0.0.1', 27015, passwd='lilith_is_hot') as client:
        response = client.run('tf_lobby_debug')
    return response.split("\n")


load_dotenv()
steam = Steam(os.environ["STEAM_WEB_API_KEY"])
_inst = TF2Lobby.spawn_from_tf_lobby_debug(test(steam), steam)
for _pl in _inst.players:
    print(f"Player '{_pl.personaname}'/{_pl.steamID64} is at {_pl.profileurl}.")
