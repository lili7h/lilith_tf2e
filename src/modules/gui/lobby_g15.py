import json
import pathlib
import time

import jsonschema

from src.modules.tf2e.lobby import TF2Player, DummyTF2Player
from src.modules.gui import G15_LOBBY_VIEWER_VER_STR
from src.modules.tf2e.main import TF2eLoader
from src.modules.g15parser.consumer import Team
from src.modules.rc.proc_reporter import is_hl2_running, get_hl2_pid
from src.modules.gui.api import MACAPI, get_player_data, get_game_data, get_app_preferences, update_player_data, \
    update_app_preferences, is_event_registered, register_event_handler
from src.modules.caching.avatar_cache import AvCache
from src.modules.tf2e import lobby

from pathlib import Path
from datetime import datetime, timedelta
from typing import Literal
from PIL import Image
from loguru import logger
from jsonschema import validate
from yaml import safe_load
from steamid_converter import Converter

import tkinter as tk
import PySimpleGUI as sg

sg.theme("DarkPurple7")
TF2_LOGO_B64 = ""

API_BASE = "http://127.0.0.1"
API_PORT = 5000

"""
Player Dict
{
  "isSelf": True/False
  "name": "xyz",
  "steamID64": "foobar",
  "steamInfo": {
    "accountName": "abc",
    "pfp": "https://avatars.steamstatic.com/",
    "vacBans": "xyz",
    "isFriend": True/False,
    ...
  },
  "gameInfo": {
    "team": 3,
    "ping": 64,
    "kills": 0,
    "deaths": 0,
    // others...
  },
  "customData": { ... },
  "tags": ["...", "..."]
}
"""


def load_steam_conf(data_path: Path) -> dict:
    with open(str(data_path.joinpath("config.yml")), 'r') as h:
        _data = safe_load(h)
    return _data["steam"]


class G15Viewer:
    """
    Sample UI layout in good old ascii art
    `┌──────────────────────────────────┐`
    `││sync│ │update│ │github│ │about│  │`
    `├──────────────────────────────────┤`
    `│┌──────────┐ ┌────────┐ ┌────────┐│`
    `││  Lilith  │ │ Team 1 │ │ Team 2 ││`
    `││  G15V v3 │ ├────────┤ ├────────┤│`
    `│├──────────┤ │        │ │        ││`
    `││          │ │        │ │        ││`
    `││ selected │ │        │ │        ││`
    `││ players  │ │        │ │        ││`
    `││ stats    │ │        │ │        ││`
    `│└──────────┘ └────────┘ └────────┘│`
    `└──────────────────────────────────┘`

    TODO:
        - Implement an on-launch font installer to load `data/fonts/*` into the font space for PySimpleGUI/TKinter
    """
    RED_TEAM_PLAYER_HEADER_KEY: str = "redTeamPlayerHeader"
    RED_TEAM_PLAYER_HEADER_IMG: Path = None  # 420 x 100
    RED_TEAM_PLAYER_TILEBG_KEY: str = "bluTeamPlayerTileBG"
    RED_TEAM_PLAYER_TILEBG_IMG: Path = None  # 420 x 140

    BLU_TEAM_PLAYER_HEADER_KEY: str = "bluTeamPlayerHeader"
    BLU_TEAM_PLAYER_HEADER_IMG: Path = None  # 420 x 100
    BLU_TEAM_PLAYER_TILEBG_KEY: str = "bluTeamPlayerTileBG"
    BLU_TEAM_PLAYER_TILEBG_IMG: Path = None  # 420 x 140

    UNKNOWN_PLAYER_ICON_KEY: str = "unknownPlayerIcon"
    BOT_PLAYER_ICON_KEY: str = "botPlayerIcon"
    CHEATER_PLAYER_ICON_KEY: str = "cheaterPlayerIcon"
    SUS_PLAYER_ICON_KEY: str = "susPlayerIcon"
    TRUSTED_PLAYER_ICON_KEY: str = "trustedPlayerIcon"
    FRIEND_PLAYER_ICON_KEY: str = "friendPlayerIcon"

    UNKNOWN_PLAYER_ICON_IMG: Path = None  # 64x64
    BOT_PLAYER_ICON_IMG: Path = None  # 64x64
    CHEATER_PLAYER_ICON_IMG: Path = None  # 64x64
    SUS_PLAYER_ICON_IMG: Path = None  # 64x64
    TRUSTED_PLAYER_ICON_IMG: Path = None  # 64x64
    FRIEND_PLAYER_ICON_IMG: Path = None  # 64x64

    LOBBY_DETAILS_IMG: Path = None
    ABOUT_HEADER_KEY: str = "aboutHeader"
    ABOUT_HEADER_IMG: Path = None

    DETAILS_HEADER_KEY: str = "detailsHeaderImage"
    DETAILS_HEADER_IMG: Path = None

    DETAILS_NAME_KEY: str = 'nameSelectedPlayer'
    DETAILS_SID_KEY: str = 'sid3SelectedPlayer'
    DETAILS_SID64_KEY: str = 'sid64SelectedPlayer'
    DETAILS_PURL_KEY: str = 'purlSelectedPlayer'
    DETAILS_LOC_KEY: str = 'locSelectedPlayer'
    DETAILS_CREATED_KEY: str = 'createdSelectedPlayer'
    DETAILS_VAC_KEY: str = 'vacSelectedPlayer'

    graph_lobby: sg.Graph = None
    graphs_red: list[sg.Graph] = None
    graphs_red_ids: list[dict] = None
    graphs_blue: list[sg.Graph] = None
    graphs_blue_ids: list[dict] = None

    player_mappings: dict[str, dict] = None
    player_tile_ids: dict[str, dict[str, int | TF2Player]] = None
    graph_tile_ids: list = None
    av_cache: AvCache = None
    steam_data: dict = None

    window: sg.Window = None
    loader: TF2eLoader = None
    lobby = None
    last_update: datetime = None

    validation_schemas: dict[str, dict] = None

    def __init__(self, data_path: Path) -> None:
        self.RED_TEAM_PLAYER_TILEBG_IMG = data_path.joinpath("images/icons/player_tile_red.png")
        self.BLU_TEAM_PLAYER_TILEBG_IMG = data_path.joinpath("images/icons/player_tile_blue.png")

        self.BLU_TEAM_PLAYER_HEADER_IMG = data_path.joinpath("images/icons/blue_team_header.png")
        self.RED_TEAM_PLAYER_HEADER_IMG = data_path.joinpath("images/icons/red_team_header.png")

        self.UNKNOWN_PLAYER_ICON_IMG = data_path.joinpath("images/icons/unknown_icon.png")
        self.BOT_PLAYER_ICON_IMG = data_path.joinpath("images/icons/bot_icon.png")
        self.CHEATER_PLAYER_ICON_IMG = data_path.joinpath("images/icons/cheater_icon.png")
        self.SUS_PLAYER_ICON_IMG = data_path.joinpath("images/icons/sus_icon.png")
        self.TRUSTED_PLAYER_ICON_IMG = data_path.joinpath("images/icons/trusted_icon.png")
        self.FRIEND_PLAYER_ICON_IMG = data_path.joinpath("images/icons/friend_icon.png")

        self.ABOUT_HEADER_IMG = data_path.joinpath("images/icons/about_v050a.png")
        self.LOBBY_DETAILS_IMG = data_path.joinpath("images/icons/lobby_details.png")
        self.DETAILS_HEADER_IMG = data_path.joinpath("images/icons/details_header.png")

        self.player_mappings = {}
        self.graph_tile_ids = []
        self.player_tile_ids = {}
        self.steam_data = load_steam_conf(data_path)

        self.data_path = data_path
        self.av_cache = AvCache(data_path.joinpath("cache/avatars/"))
        self.av_cache.check_tf2_small_in_cache(data_path)
        self.api = MACAPI(f"{API_BASE}:{API_PORT}")

        self.validation_schemas = {}
        _json_schemas = pathlib.Path(data_path.joinpath("schemas/")).glob("*.json")
        for _sc in _json_schemas:
            _name = _sc.name.split("validate_")[1].replace(".json", "")
            with open(str(_sc), 'r') as h:
                self.validation_schemas[_name] = json.loads(h.read())

        _frame = self.build_layout()
        self.window = sg.Window("Testing", layout=[[_frame]], resizable=True, finalize=True)
        self.set_detail_data_column_style()

        self.run_loop()

    def run_loop(self):
        while True:
            event, values = self.window.read(timeout=125)
            if event == sg.WIN_CLOSED:
                break
            elif event != sg.TIMEOUT_EVENT:
                if str(event).startswith("testGraph") and str(event).endswith("+UP"):
                    _pl = self.player_mappings[str(event).replace("+UP", "")]
                    self.update_player_details(_pl)

            if self.last_update is None or (datetime.now() - self.last_update).seconds > 5:
                logger.info("Updating player cards")
                self.update_player_cards()
                self.last_update = datetime.now()

            self.window.refresh()

    def update_player_cards(self):
        self.hide_all_graphs()
        _game = get_game_data(self.api)

        # if "server" in _game:
        #     _game = _game["server"]

        _players = _game["players"]
        # logger.info(f"num players: {len(_players)}")

        _players_red = [x for x in _players if x["gameInfo"]["team"] == Team.Red.value]
        _players_blu = [x for x in _players if x["gameInfo"]["team"] == Team.Blue.value]

        # logger.info(f"num red players: {len(_players_red)}")
        # logger.info(f"num blue players: {len(_players_blu)}")

        _updated_highest_blu = 0
        _updated_highest_red = 0

        try:
            for idx, _pl in enumerate(_players_blu):
                self.graphs_blue_ids[idx] = self.build_player_tile(self.graphs_blue[idx], _pl)
                _updated_highest_blu = idx
        except IndexError:
            logger.warning("Attempting to graph more players than there are graphs. "
                           "Support only extends to <=32 player severs.")

        try:
            for idx, _pl in enumerate(_players_red):
                self.graphs_red_ids[idx] = self.build_player_tile(self.graphs_red[idx], _pl)
                _updated_highest_red = idx
        except IndexError:
            logger.warning("Attempting to graph more players than there are graphs. "
                           "Support only extends to <=32 player severs.")

        self.update_server_details(_game, (_updated_highest_blu + 1, _updated_highest_red + 1))

    @staticmethod
    def _resize_image(image_path: str) -> str:
        img = (Image.open(image_path))
        resized = img.resize((64, 64), Image.LANCZOS)
        _new_path = image_path.replace(".png", "_64.png")
        resized.save(_new_path)
        return _new_path

    @staticmethod
    def make_server_details_graph() -> sg.Graph:
        graph = sg.Graph(
            canvas_size=(840, 200), graph_bottom_left=(0, 0), graph_top_right=(840, 200), enable_events=True,
            drag_submits=True, key=f"lobbyServerDetailsGraph"
        )
        return graph

    @staticmethod
    def make_graphs(team: Literal['red', 'blu']) -> list[sg.Graph]:
        graphs = []
        for i in range(16):
            graph = sg.Graph(
                canvas_size=(420, 140), graph_bottom_left=(0, 0), graph_top_right=(420, 140), enable_events=True,
                drag_submits=True, key=f"testGraph{team}{i}"
            )
            graphs.append(graph)
        return graphs

    def make_player_columns(self) -> tuple[sg.Column, sg.Column]:
        self.graphs_red = self.make_graphs('red')
        self.graphs_blue = self.make_graphs('blu')
        self.graphs_red_ids = [{}] * 16
        self.graphs_blue_ids = [{}] * 16
        _column_red = sg.Column(
            layout=[[x] for x in self.graphs_red],
            # scrollable=True,
            # vertical_scroll_only=True,
            # size=(430, 800),
            key="redTeamPlayerTilesColumn"
        )
        _column_blu = sg.Column(
            layout=[[x] for x in self.graphs_blue],
            # scrollable=True,
            # vertical_scroll_only=True,
            # size=(430, 800),
            key="bluTeamPlayerTilesColumn"
        )
        return _column_blu, _column_red

    def update_player_details(self, player: dict) -> None:
        _name: sg.InputText = self.window[self.DETAILS_NAME_KEY]
        _sid: sg.InputText = self.window[self.DETAILS_SID_KEY]
        _sid64: sg.InputText = self.window[self.DETAILS_SID64_KEY]
        _purl: sg.InputText = self.window[self.DETAILS_PURL_KEY]
        _created: sg.InputText = self.window[self.DETAILS_CREATED_KEY]
        _loc: sg.InputText = self.window[self.DETAILS_LOC_KEY]
        _vac: sg.InputText = self.window[self.DETAILS_VAC_KEY]

        _name.update(value=player["name"])
        _sid.update(value=Converter.to_steamID3(player["steamID64"]))
        _sid64.update(value=player["steamID64"])
        _purl.update(value=f"https://steamcommunity.com/profiles/{player['steamID64']}/")
        _created.update(value=str(datetime.fromtimestamp(player['steamInfo']['timecreated'])))
        _loc.update(value=player['steamInfo']['loccountrycode'])
        _vac.update(value=" --not implemented-- ")

    def update_server_details(self, game_obj: dict, num_players_by_team: tuple[int, int]) -> None:
        SERVER_DETAILS_TILE_HEIGHT = 200
        SERVER_DETAILS_TILE_WIDTH = 840

        for id_ in self.graph_tile_ids:
            self.graph_lobby.delete_figure(id_)

        _map = game_obj["map"]
        _ip = game_obj["ip"]
        _hostname = game_obj["hostname"]
        _players = f'{game_obj["numPlayers"]} / {game_obj["maxPlayers"]}'
        _gamemode = game_obj["gamemode"]["type"] \
                    + (" (matchmade)" if game_obj["gamemode"]["matchmaking"] else "") \
                    + (" (vanilla)" if game_obj["gamemode"]["vanilla"] else "")

        self.graph_tile_ids = []

        self.graph_tile_ids.append(self.graph_lobby.draw_image(filename=str(self.LOBBY_DETAILS_IMG),
                                                               location=(0, SERVER_DETAILS_TILE_HEIGHT)))
        self.graph_tile_ids.append(
            self.graph_lobby.draw_text(text=_map,
                                       location=(SERVER_DETAILS_TILE_WIDTH / 2, SERVER_DETAILS_TILE_HEIGHT / 2),
                                       color='white', font='CIKANDEI 18', text_location=sg.TEXT_LOCATION_LEFT))
        self.graph_tile_ids.append(
            self.graph_lobby.draw_text(text=_ip,
                                       location=(SERVER_DETAILS_TILE_WIDTH / 2, SERVER_DETAILS_TILE_HEIGHT / 1.62),
                                       color='white', font='CIKANDEI 18', text_location=sg.TEXT_LOCATION_LEFT))
        self.graph_tile_ids.append(
            self.graph_lobby.draw_text(text=_hostname,
                                       location=(SERVER_DETAILS_TILE_WIDTH / 2, SERVER_DETAILS_TILE_HEIGHT / 1.36),
                                       color='white', font='CIKANDEI 18', text_location=sg.TEXT_LOCATION_LEFT))
        self.graph_tile_ids.append(
            self.graph_lobby.draw_text(text=_gamemode,
                                       location=(SERVER_DETAILS_TILE_WIDTH / 2, SERVER_DETAILS_TILE_HEIGHT / 2.62),
                                       color='white', font='CIKANDEI 18', text_location=sg.TEXT_LOCATION_LEFT))
        self.graph_tile_ids.append(
            self.graph_lobby.draw_text(text=_players,
                                       location=(SERVER_DETAILS_TILE_WIDTH / 2, SERVER_DETAILS_TILE_HEIGHT * 0.26),
                                       color='white', font='CIKANDEI 18', text_location=sg.TEXT_LOCATION_LEFT))
        self.graph_tile_ids.append(
            self.graph_lobby.draw_text(text=str(num_players_by_team[0]),
                                       location=(SERVER_DETAILS_TILE_WIDTH * 0.16, SERVER_DETAILS_TILE_HEIGHT * 0.1),
                                       color='white', font='CIKANDEI 18', text_location=sg.TEXT_LOCATION_LEFT))
        self.graph_tile_ids.append(
            self.graph_lobby.draw_text(text=str(num_players_by_team[1]),
                                       location=(SERVER_DETAILS_TILE_WIDTH * 0.95, SERVER_DETAILS_TILE_HEIGHT * 0.1),
                                       color='white', font='CIKANDEI 18', text_location=sg.TEXT_LOCATION_LEFT))
        self.graph_tile_ids.append(
            self.graph_lobby.draw_text(text=f'Name: {self.steam_data["name"]}',
                                       location=(SERVER_DETAILS_TILE_WIDTH * 0.02, SERVER_DETAILS_TILE_HEIGHT * 0.78),
                                       color='white', font='CIKANDEI 18', text_location=sg.TEXT_LOCATION_LEFT))
        self.graph_tile_ids.append(
            self.graph_lobby.draw_text(text=f"ID: {self.steam_data['steamid64']}",
                                       location=(SERVER_DETAILS_TILE_WIDTH * 0.055, SERVER_DETAILS_TILE_HEIGHT * 0.66),
                                       color='white', font='CIKANDEI 18', text_location=sg.TEXT_LOCATION_LEFT))

    def make_player_lists(self) -> sg.Column:
        self.graph_lobby = self.make_server_details_graph()
        _column_blu, _column_red = self.make_player_columns()
        _combined_columns = sg.Column(
            layout=[
                [
                    sg.Stretch(), self.graph_lobby, sg.Stretch()
                ],
                [
                    sg.Image(filename=str(self.BLU_TEAM_PLAYER_HEADER_IMG)),
                    sg.Stretch(),
                    sg.Image(filename=str(self.RED_TEAM_PLAYER_HEADER_IMG))
                ],
                [
                    sg.Column(
                        layout=[[_column_blu, _column_red]]
                    )
                ]
            ],
            size=(900, 800),
            scrollable=True,
            vertical_scroll_only=True,
        )

        # _expand_blue = sg.Column(
        #     layout=[
        #         [sg.Image(filename=str(self.BLU_TEAM_PLAYER_HEADER_IMG))],
        #         [_column_blu]
        #     ]
        # )
        # _expand_red = sg.Column(
        #     layout=[
        #         [sg.Image(filename=str(self.RED_TEAM_PLAYER_HEADER_IMG))],
        #         [_column_red]
        #     ]
        # )
        return sg.Column(
            layout=[[_combined_columns]]
        )

    def hide_all_graphs(self) -> None:
        for idx, _g in enumerate(self.graphs_blue):
            _g.update(visible=False)
            if self.graphs_blue_ids[idx] != {}:
                for _k in self.graphs_blue_ids[idx]:
                    _g.delete_figure(self.graphs_blue_ids[idx][_k])
                self.graphs_blue_ids[idx] = {}

        for idx, _g in enumerate(self.graphs_red):
            _g.update(visible=False)
            if self.graphs_red_ids[idx] != {}:
                for _k in self.graphs_red_ids[idx]:
                    _g.delete_figure(self.graphs_red_ids[idx][_k])
                self.graphs_red_ids[idx] = {}

    def build_player_tile(self, graph: sg.Graph, player: dict) -> dict:
        MAX_NAME_LEN = 20
        PLAYER_TILE_WIDTH = 420
        PLAYER_TILE_HEIGHT = 140

        try:
            validate(player, schema=self.validation_schemas['player'])
        except jsonschema.ValidationError as e:
            logger.warning(f"JSON Validation failure at: {e.message}")
            logger.warning(f"Player object failed to validate! Ignoring...")
            return {}

        graph.update(visible=True)
        _name = player["name"]

        _fn = None
        if player["gameInfo"]["team"] == Team.Blue.value:
            _fn = self.BLU_TEAM_PLAYER_TILEBG_IMG
        else:
            _fn = self.RED_TEAM_PLAYER_TILEBG_IMG

        _img_id = graph.draw_image(
            filename=str(_fn),
            location=(0, PLAYER_TILE_HEIGHT),
        )

        # Custom tagging for sexy icons
        _association_str = player["customData"]["tag"] if "tag" in player["customData"] else "unknown"

        _association_icon_id = graph.draw_image(
            filename=str(self.UNKNOWN_PLAYER_ICON_IMG).replace("unknown", _association_str),  #
            location=(PLAYER_TILE_WIDTH / 1.53, PLAYER_TILE_HEIGHT / 2)
        )

        _av_hash = player["steamInfo"]["pfphash"] if player["steamInfo"] is not None else "tf2small"

        img_path = self._resize_image(str(self.av_cache.get_image(_av_hash)))
        _pfp_icon_id = graph.draw_image(
            filename=img_path,
            location=(PLAYER_TILE_WIDTH / 6.6, PLAYER_TILE_HEIGHT / 2)
        )

        if len(_name) > MAX_NAME_LEN:  # truncate name when too long
            _name = _name[:MAX_NAME_LEN] + "..."

        _name_id = graph.draw_text(text=_name,
                                   location=(PLAYER_TILE_WIDTH / 1.83, PLAYER_TILE_HEIGHT / 1.3),
                                   color='white', font='CIKANDEI 32')
        _ping_id = graph.draw_text(text=f"{player['gameInfo']['ping']}ms",
                                   location=(PLAYER_TILE_WIDTH / 1.91, PLAYER_TILE_HEIGHT / 2.8),
                                   color='white', font='CIKANDEI 24')
        _time_id = graph.draw_text(text=str(timedelta(seconds=player['gameInfo']['time'])),
                                   location=(PLAYER_TILE_WIDTH / 2, PLAYER_TILE_HEIGHT / 7),
                                   color='white', font='CIKANDEI 24')
        self.player_tile_ids[player["steamID64"]] = {
            "name": _name_id,
            "ping": _ping_id,
            "time": _time_id,
            "pfp": _pfp_icon_id,
            "association": _association_icon_id,
            "bg": _img_id,
            "player": player,
        }
        self.player_mappings[graph.key] = player
        return self.player_tile_ids[player["steamID64"]]

    def left_wing(self) -> sg.Column:
        return sg.Column(
            layout=[
                [sg.Image(filename=str(self.ABOUT_HEADER_IMG), key=self.ABOUT_HEADER_KEY)],
                [sg.Image(filename=str(self.DETAILS_HEADER_IMG), key=self.DETAILS_HEADER_KEY)],
                [sg.Column(layout=[[self.create_detail_labels_column(), self.create_detail_data_column()]])],
            ]
        )

    def create_detail_data_column(self) -> sg.Column:
        _col = sg.Column(
            layout=[
                [sg.InputText("", key=self.DETAILS_NAME_KEY, use_readonly_for_disable=True, disabled=True)],
                [sg.InputText("", key=self.DETAILS_SID_KEY, use_readonly_for_disable=True, disabled=True)],
                [sg.InputText("", key=self.DETAILS_SID64_KEY, use_readonly_for_disable=True, disabled=True)],
                [sg.InputText("", key=self.DETAILS_PURL_KEY, use_readonly_for_disable=True, disabled=True)],
                [sg.InputText("", key=self.DETAILS_LOC_KEY, use_readonly_for_disable=True, disabled=True)],
                [sg.InputText("", key=self.DETAILS_CREATED_KEY, use_readonly_for_disable=True, disabled=True)],
                [sg.InputText("", key=self.DETAILS_VAC_KEY, use_readonly_for_disable=True, disabled=True)],
            ]
        )
        return _col

    @staticmethod
    def create_detail_labels_column() -> sg.Column:
        return sg.Column(
            layout=[[sg.Text("Name:")], [sg.Text("SteamID3:")], [sg.Text("SteamID64:")], [sg.Text("Profile:")],
                    [sg.Text("Location:")], [sg.Text("Created:")], [sg.Text("VAC:")]],
            element_justification='right'
        )

    def build_layout(self) -> sg.Frame:
        return sg.Frame(
            title="",
            layout=[
                [self.left_wing(), self.make_player_lists()]
            ]
        )

    def set_detail_data_column_style(self) -> None:
        _key_names = [
            self.DETAILS_NAME_KEY,
            self.DETAILS_SID_KEY,
            self.DETAILS_SID64_KEY,
            self.DETAILS_PURL_KEY,
            self.DETAILS_CREATED_KEY,
            self.DETAILS_LOC_KEY,
            self.DETAILS_VAC_KEY,
        ]
        for _k in _key_names:
            self.window[_k].Widget.config(readonlybackground=sg.theme_background_color())
            self.window[_k].Widget.config(borderwidth=0)


if __name__ == "__main__":
    _data_path = Path("../../../data/")
    _inst = G15Viewer(_data_path)
