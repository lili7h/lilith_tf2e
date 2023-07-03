from src.modules.tf2e.lobby import TF2Player, DummyTF2Player
from src.modules.gui import G15_LOBBY_VIEWER_VER_STR
from src.modules.tf2e.main import TF2eLoader
from src.modules.g15parser.consumer import Team
from src.modules.rc.proc_reporter import is_hl2_running, get_hl2_pid
from src.modules.caching.avatar_cache import AvCache
from src.modules.tf2e import lobby

from pathlib import Path
from datetime import datetime
from typing import Literal
from PIL import Image

import tkinter as tk
import PySimpleGUI as sg

sg.theme("DarkPurple7")
TF2_LOGO_B64 = ""


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

    graphs_red: list[sg.Graph] = None
    graphs_red_ids: list[dict] = None
    graphs_blue: list[sg.Graph] = None
    graphs_blue_ids: list[dict] = None

    player_mappings: dict[int, TF2Player] = None
    player_tile_ids: dict[str, dict[str, int | TF2Player]] = None
    av_cache: AvCache = None

    window: sg.Window = None
    loader: TF2eLoader = None
    lobby = None
    last_update: datetime = None

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
        self.DETAILS_HEADER_IMG = data_path.joinpath("images/icons/details_header.png")

        self.player_mappings = {}
        self.player_tile_ids = {}
        self.loader = TF2eLoader(data_path)
        self.lobby = lobby.LobbyWatching(self.loader.rcon_client, self.loader.steam_client)
        self.lobby.lobby.connect_listener(self.loader.log_listener)
        self.av_cache = self.loader.av_cache
        # self.av_cache = AvCache(data_path.joinpath("cache/avadatars/"))

        _frame = self.build_layout()
        self.window = sg.Window("Testing", layout=[[_frame]], resizable=True, finalize=True)
        self.set_detail_data_column_style()

        self.last_update = datetime.now()
        self.run_loop()

    def run_loop(self):
        while True:
            event, values = self.window.read(timeout=125)
            if event == sg.WIN_CLOSED:
                break

            if self.last_update < self.lobby.lobby.last_update:
                self.update_player_cards()

            self.window.refresh()

    def update_player_cards(self):
        self.hide_all_graphs()
        _players_red = [x for x in self.lobby.lobby.players if x.game_team == Team.Red]
        _players_blu = [x for x in self.lobby.lobby.players if x.game_team == Team.Blue]
        _updated_highest_blu = 0
        _updated_highest_red = 0

        for idx, _pl in enumerate(_players_blu):
            self.graphs_blue_ids[idx] = self.build_player_tile(self.graphs_blue[idx], _pl)
            _updated_highest_blu = idx

        for idx, _pl in enumerate(_players_red):
            self.graphs_red_ids[idx] = self.build_player_tile(self.graphs_red[idx], _pl)
            _updated_highest_red = idx

    @staticmethod
    def _resize_image(image_path: str) -> str:
        img = (Image.open(image_path))
        resized = img.resize((64, 64), Image.LANCZOS)
        _new_path = image_path.replace(".png", "_64.png")
        resized.save(_new_path)
        return _new_path

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
        self.graphs_red_ids = [{}]*16
        self.graphs_blue_ids = [{}]*16
        _column_red = sg.Column(
            layout=[[x] for x in self.graphs_red],
            scrollable=True,
            vertical_scroll_only=True,
            size=(430, 800),
            key="redTeamPlayerTilesColumn"
        )
        _column_blu = sg.Column(
            layout=[[x] for x in self.graphs_blue],
            scrollable=True,
            vertical_scroll_only=True,
            size=(430, 800),
            key="bluTeamPlayerTilesColumn"
        )
        return _column_blu, _column_red

    def make_player_lists(self) -> sg.Column:
        _column_blu, _column_red = self.make_player_columns()
        _expand_blue = sg.Column(
            layout=[
                [sg.Image(filename=str(self.BLU_TEAM_PLAYER_HEADER_IMG))],
                [_column_blu]
            ]
        )
        _expand_red = sg.Column(
            layout=[
                [sg.Image(filename=str(self.RED_TEAM_PLAYER_HEADER_IMG))],
                [_column_red]
            ]
        )
        return sg.Column(
            layout=[[_expand_blue, _expand_red]]
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

    def build_player_tile(self, graph: sg.Graph, player: TF2Player) -> dict:
        MAX_NAME_LEN = 24
        PLAYER_TILE_WIDTH = 420
        PLAYER_TILE_HEIGHT = 140

        graph.update(visible=True)
        _name = player.personaname

        _fn = None
        if player.game_team == Team.Blue:
            _fn = self.BLU_TEAM_PLAYER_TILEBG_IMG
        else:
            _fn = self.RED_TEAM_PLAYER_TILEBG_IMG

        _img_id = graph.draw_image(
            filename=str(_fn),
            location=(0, PLAYER_TILE_HEIGHT),
        )
        _association_icon_id = graph.draw_image(
            filename=str(self.UNKNOWN_PLAYER_ICON_IMG).replace("unknown", player.association.icon_str),
            location=(PLAYER_TILE_WIDTH / 1.53, PLAYER_TILE_HEIGHT / 2)
        )
        img_path = self._resize_image(str(self.av_cache.get_image(player.avatarhash)))
        _pfp_icon_id = graph.draw_image(
            filename=img_path,
            location=(PLAYER_TILE_WIDTH / 6.6, PLAYER_TILE_HEIGHT / 2)
        )

        if len(_name) > MAX_NAME_LEN:  # truncate name when too long
            _name = _name[:MAX_NAME_LEN] + "..."

        _name_id = graph.draw_text(text=_name,
                                   location=(PLAYER_TILE_WIDTH / 1.83, PLAYER_TILE_HEIGHT / 1.3),
                                   color='white', font='CIKANDEI 32')
        _ping_id = graph.draw_text(text=f"{player.ping}ms",
                                   location=(PLAYER_TILE_WIDTH / 1.91, PLAYER_TILE_HEIGHT / 2.8),
                                   color='white', font='CIKANDEI 24')
        _time_id = graph.draw_text(text=player.game_time,
                                   location=(PLAYER_TILE_WIDTH / 2, PLAYER_TILE_HEIGHT / 7),
                                   color='white', font='CIKANDEI 24')
        self.player_tile_ids[player.steamID64] = {
            "name": _name_id,
            "ping": _ping_id,
            "time": _time_id,
            "pfp": _pfp_icon_id,
            "association": _association_icon_id,
            "bg": _img_id,
            "player": player,
        }
        return self.player_tile_ids[player.steamID64]

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
                [sg.InputText("", key=self.DETAILS_CREATED_KEY, use_readonly_for_disable=True, disabled=True)],
                [sg.InputText("", key=self.DETAILS_LOC_KEY, use_readonly_for_disable=True, disabled=True)],
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


def create_header_button_row() -> sg.Frame:
    return sg.Frame(
        layout=[
            [sg.Button(button_text="Sync", key="syncBtn", font="Any 16", expand_x=True),
             sg.Button(button_text="Update", key="updateBtn", font="Any 16", expand_x=True),
             sg.Button(button_text="Github", key="githubBtn", font="Any 16", expand_x=True),
             sg.Button(button_text="About", key="aboutBtn", font="Any 16", expand_x=True)]
        ],
        title="",
        expand_x=True,
        relief='raised',
        border_width=2
    )


def create_player_listing_frame(team: Literal[1, 2]) -> sg.Frame:
    return sg.Frame(
        title=f"Team {team}",
        key=f"playerListingFrame{team}",
        layout=[
            [create_player_listing_column(team)]
        ]
    )


def create_player_listing_column(team: Literal[1, 2]) -> sg.Column:
    _team_frames = []
    for i in range(16):
        _dummy = DummyTF2Player(team * 100 + i)
        _frame = create_player_tile(team * 100 + i, _dummy)
        _team_frames.append(_frame)
    return sg.Column(
        layout=[[x] for x in _team_frames],
        key=f"playerTilesColumn{team}",
        scrollable=True,
        expand_y=True,
        expand_x=True,
        vertical_scroll_only=True,
        size=(450, 600),
    )


def create_player_tile(tile_id: int, player: TF2Player | DummyTF2Player) -> sg.Frame:
    # TODO: Player tiles may have to be changed
    player_tile_text_plate = sg.Column([
        [
            sg.Text(player, key=f"playerNamePlate{tile_id}", font='Any 14', expand_x=True),

        ],
        [
            sg.Text(text=f"{player.pl_score} / {player.pl_deaths}", font='Any 10', expand_x=True,
                    key=f"playerScorePlate{tile_id}"),
            sg.Text(player.game_time, key=f"playerTimePlate{tile_id}", font='Any 12', expand_x=True),
            sg.Text(player.ping, key=f"playerPingPlate{tile_id}", font='Any 12', expand_x=True)
        ]
    ], expand_x=True)

    # TODO: call async image download if player.pfp_cached == False, leave image as default TF2 logo and set cached to
    #       true. When player updates occur, we will check for if the cached image exists locally on the drive yet,
    #       and update the image source then.

    player_tile_plate = [
        [
            sg.pin(
                elem=sg.Image(
                    data=TF2_LOGO_B64.encode('utf8'), subsample=32, key=f"playerIconPlate{tile_id}",
                    enable_events=True,
                ),
                shrink=False,
            ),
            player_tile_text_plate,
            sg.pin(
                elem=sg.Combo(
                    readonly=True, key=f"playerAssociationCombo{tile_id}", font="Any 10",
                    values=TF2Player.possible_associations, default_value=player.association, enable_events=True,
                    expand_x=False
                ),
                shrink=False
            )
        ]
    ]

    _frame = sg.Frame(layout=player_tile_plate, title=f"", key=f"playerTileFrame{tile_id}",
                      title_location=sg.TITLE_LOCATION_BOTTOM_RIGHT, relief='sunken', expand_x=True,
                      element_justification='right', size=(450, 70), visible=False)

    return _frame


def about_and_status() -> sg.Frame:
    # TODO: clean up how we generate the about and status frames.
    headerDataColumn = sg.Column([
        [sg.Text(f"G15 Lobby Viewer {G15_LOBBY_VIEWER_VER_STR}", justification="center", font="Any 20")],
        [sg.Text("Created by Lilith", font="Any 16", justification="center", text_color="white")],
        [sg.Text("(C) 2023, MIT License", font="Any 12", justification="center", text_color="white")],
    ])

    headerLayout = [
        [sg.Image(source=str(Path("../../../data/images/lilith.png")), subsample=16), headerDataColumn]
    ]

    headerFrame = sg.Frame(title="About", layout=headerLayout, expand_x=True)

    TF2StatusColumn = sg.Column([
        [sg.Text("TF2 is %status%", text_color="red", key="tf2statuselem")],
        [sg.Text("PID:"), sg.Text("-none-", key="tf2pidkey")],
        [sg.Text("Steam Con:"), sg.Text("-none-", key="steamstatuskey", text_color="red")]
    ])

    statusLayout = [
        [sg.Image(data=TF2_LOGO_B64.encode('utf8'), subsample=16), TF2StatusColumn]
    ]

    statusFrame = sg.Frame(title="Status", layout=statusLayout, expand_x=True)

    return sg.Frame(
        title="",
        layout=[[headerFrame], [statusFrame]],
        key="headerFrame",
    )


def hide_all_player_tiles(window: sg.Window) -> None:
    for i in range(16):
        for team in range(1, 3):
            _tid = team * 100 + i
            _name: sg.Text = window[f"playerNamePlate{_tid}"]
            _time: sg.Text = window[f"playerTimePlate{_tid}"]
            _ping: sg.Text = window[f"playerPingPlate{_tid}"]
            _icon: sg.Image = window[f"playerIconPlate{_tid}"]
            _combo: sg.Combo = window[f"playerAssociationCombo{_tid}"]

            _name.update(value="")
            _time.update(value="")
            _ping.update(value="")
            # TODO: update icon somehow

            window[f"playerTileFrame{_tid}"].update(visible=False)


def update_player_tile(window: sg.Window, player_id: int, team: Literal[1, 2], player: TF2Player) -> None:
    _db = AvCache(Path("NULL"))
    img_path = _db.get_image(player.avatarhash)
    if img_path is None:
        _db.cache_image(player.avatarhash, player.avatarfull)

    _tid = team * 100 + player_id
    _name: sg.Text = window[f"playerNamePlate{_tid}"]
    _time: sg.Text = window[f"playerTimePlate{_tid}"]
    _ping: sg.Text = window[f"playerPingPlate{_tid}"]
    _score: sg.Text = window[f"playerScorePlate{_tid}"]
    _icon: sg.Image = window[f"playerIconPlate{_tid}"]
    _combo: sg.Combo = window[f"playerAssociationCombo{_tid}"]

    _name.update(value=player.personaname, visible=True, text_color=player.association.color)
    _time.update(value=player.game_time, visible=True)
    _ping.update(value=f"{player.ping}ms", visible=True)
    _score.update(value=f"{player.pl_score} / {player.pl_deaths}")
    if img_path is not None:
        _icon.update(visible=True, source=str(img_path), subsample=3)

    # print(_img_b64_stream)
    # TODO: update icon somehow
    _combo.update(value=player.association, visible=True)

    window[f"playerTileFrame{_tid}"].update(visible=True)


def create_detail_labels_column() -> sg.Column:
    return sg.Column(
        layout=[[sg.Text("Name:")], [sg.Text("SteamID3:")], [sg.Text("SteamID64:")], [sg.Text("Profile:")],
                [sg.Text("Location:")], [sg.Text("Created:")], [sg.Text("VAC:")]]
    )


def get_detail_data_column_keys() -> list[str]:
    return [
        f'nameSelectedPlayer',
        f'sid3SelectedPlayer',
        f'sid64SelectedPlayer',
        f'purlSelectedPlayer',
        f'locSelectedPlayer',
        f'createdSelectedPlayer',
        f'vacSelectedPlayer',
    ]


def set_detail_data_column_style(window: sg.Window) -> None:
    _key_names = get_detail_data_column_keys()
    for _k in _key_names:
        window[_k].Widget.config(readonlybackground=sg.theme_background_color())
        window[_k].Widget.config(borderwidth=0)


def create_detail_data_column() -> sg.Column:
    _key_names = get_detail_data_column_keys()
    _col = sg.Column(
        layout=[
            [sg.InputText("(null)", key=_key_names[0], use_readonly_for_disable=True, disabled=True)],
            [sg.InputText("(null)", key=_key_names[1], use_readonly_for_disable=True, disabled=True)],
            [sg.InputText("(null)", key=_key_names[2], use_readonly_for_disable=True, disabled=True)],
            [sg.InputText("(null)", key=_key_names[3], use_readonly_for_disable=True, disabled=True)],
            [sg.InputText("(null)", key=_key_names[4], use_readonly_for_disable=True, disabled=True)],
            [sg.InputText("(null)", key=_key_names[5], use_readonly_for_disable=True, disabled=True)],
            [sg.InputText("(null)", key=_key_names[6], use_readonly_for_disable=True, disabled=True)],
        ]
    )
    return _col


def create_detail_data_frame() -> sg.Frame:
    return sg.Frame(
        layout=[
            [create_detail_labels_column(), create_detail_data_column()]
        ],
        title=f"Advanced Details",
        element_justification="left",
        key=f"selectedPlayerListFrame",
        expand_x=True, expand_y=True,
    )


def update_player_details(window: sg.Window, player: TF2Player) -> None:
    _ident = f"SelectedPlayer"
    try:
        _pl_tc = datetime.fromtimestamp(player.timecreated)
    except TypeError:
        _pl_tc = "unknown"

    _vals = {"name": player.personaname,
             "sid3": player.steamID3,
             "sid64": player.steamID64,
             "purl": player.profileurl,
             "loc": player.loccountrycode,
             "created": _pl_tc,
             "vac": "--not implemented--"}

    for _k in _vals:
        window[f"{_k}{_ident}"].update(_vals[_k])

    window.refresh()


def main_layout() -> sg.Frame:
    _layout = [
        [create_header_button_row()],
        [create_player_listing_column(1),
         sg.Column(layout=[[about_and_status()], [create_detail_data_frame()]]),
         create_player_listing_column(2)]
    ]
    return sg.Frame(title="", layout=_layout)


def build_window() -> sg.Window:
    return sg.Window(
        f"G15 Lobby Viewer {G15_LOBBY_VIEWER_VER_STR}", layout=[[main_layout()]], resizable=True
    )


def update_players(window_: sg.Window, lobby_watcher: lobby.LobbyWatching) -> None:
    hide_all_player_tiles(window_)
    team1idx = 0
    team2idx = 0
    for _pl in lobby_watcher.lobby.players:
        if _pl.game_team == Team.Red:
            update_player_tile(window_, team2idx, 2, _pl)
            team2idx += 1

        elif _pl.game_team == Team.Blue:
            update_player_tile(window_, team1idx, 1, _pl)
            team1idx += 1

    _last_update: datetime = lobby_watcher.lobby.last_update

    _t1_listing_frame: sg.Column = window_['playerTilesColumn1']
    _t2_listing_frame: sg.Column = window_['playerTilesColumn2']
    _t1_listing_frame.contents_changed()
    _t2_listing_frame.contents_changed()

    window_.refresh()


def update_status(window_: sg.Window, loader: TF2eLoader) -> None:
    _tf2_status: sg.Text = window_["tf2statuselem"]
    _tf2_pid: sg.Text = window_["tf2pidkey"]
    _steam_status: sg.Text = window_["steamstatuskey"]

    if is_hl2_running:
        _tf2_status.update(value="TF2 is running!", text_color="green")
    else:
        _tf2_status.update(value="TF2 is closed :(", text_color="red")

    _tf2_pid.update(value=str(get_hl2_pid()))

    if loader.steam_client is not None:
        _steam_status.update(value="online!", text_color="green")
    else:
        _steam_status.update(value="offline :(", text_color="red")


def main(loader: TF2eLoader, lobby_watcher: lobby.LobbyWatching):
    sg.theme("DarkPurple7")
    window = build_window()

    _last_update: datetime = lobby_watcher.lobby.last_update
    window.finalize()
    while True:
        event, values = window.read(timeout=125)
        if event == sg.WIN_CLOSED:
            break
        if event and event != sg.TIMEOUT_EVENT:
            print(event)
            # TODO: Complete image click handler to updated the detail info to this user
            #       Note that the username component of the user frame stores the entire player object
            if event.startswith("playerIconPlate"):

                _tid = event.strip().replace("playerIconPlate", "")
                _name: sg.Text = window[f"playerNamePlate{_tid}"]
                _pl = lobby_watcher.lobby.get_player_by_nick(_name.get())
                print(_pl)
                if _pl is not None:
                    update_player_details(window, _pl)
                    set_detail_data_column_style(window)

        if _last_update != lobby_watcher.lobby.last_update:
            update_players(window_=window, lobby_watcher=lobby_watcher)

        update_status(window_=window, loader=loader)

        window.refresh()

    # End program
    loader.log_listener.end()
    lobby_watcher.kill_watcher()
    window.close()


if __name__ == "__main__":
    _data_path = Path("../../../data/")
    _inst = G15Viewer(_data_path)
    # client_loader = TF2eLoader(_data_path)
    # game_lobby = lobby.LobbyWatching(client_loader.rcon_client, client_loader.steam_client)
    # game_lobby.lobby.connect_listener(client_loader.log_listener)
    #
    # with open(str(_data_path.joinpath("images/tf2b64.txt")), 'r') as h:
    #     TF2_LOGO_B64 = h.read()
    #
    # main(client_loader, game_lobby)
