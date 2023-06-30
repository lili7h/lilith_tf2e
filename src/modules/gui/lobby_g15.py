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

import PySimpleGUI as sg

sg.theme("DarkPurple1")
"""
Sample UI layout in good old ascii art
 ┌──────────────────────────────────┐
 ││sync│ │update│ │github│ │about│  │ 
 ├──────────────────────────────────┤
 │┌────────┐ ┌──────────┐ ┌────────┐│
 ││ Team 1 │ │  Lilith  │ │ Team 2 ││
 │├────────┤ │  SLV v2  │ ├────────┤│
 ││        │ └──────────┘ │        ││
 ││        │ ┌──────────┐ │        ││
 ││        │ │ selected │ │        ││
 ││        │ │ players  │ │        ││ 
 ││        │ │ stats    │ │        ││
 │└────────┘ └──────────┘ └────────┘│
 └──────────────────────────────────┘
"""

TF2_LOGO_B64 = ""

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
        [sg.Text(player.personaname, key=f"playerNamePlate{tile_id}", font='Any 14', expand_x=True)],
        [
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
                    data=TF2_LOGO_B64.encode('utf8'), subsample=32, key=f"playerIconPlate{tile_id}"
                ),
                shrink=False
            ),
            player_tile_text_plate,
            sg.pin(
                elem=sg.Combo(
                    readonly=True, key=f"playerAssociationCombo{tile_id}", font="Any 10",
                    values=TF2Player.possible_associations, default_value=player.association, enable_events=True,
                    expand_x=False
                ),
                shrink=False
            ),
            sg.Checkbox(enable_events=True, key=f"playerCheckbox{tile_id}", text="")
        ]
    ]

    _frame = sg.Frame(layout=player_tile_plate, title=f"{player.loccountrycode}", key=f"playerTileFrame{tile_id}",
                      title_location=sg.TITLE_LOCATION_BOTTOM_RIGHT, relief=sg.RELIEF_RIDGE, expand_x=True,
                      element_justification='right', size=(450, 90), visible=False)

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
            _cb: sg.Checkbox = window[f"playerCheckbox{_tid}"]

            _name.update(value="")
            _time.update(value="")
            _ping.update(value="")
            # TODO: update icon somehow
            _cb.update(value=False)

            window[f"playerTileFrame{_tid}"].update(visible=False)


def update_player_tile(window: sg.Window, player_id: int, team: Literal[1, 2], player: TF2Player) -> None:
    _db = AvCache(Path("NULL"))
    _img_b64_stream = _db.get_avatar(player.avatarhash)
    if _img_b64_stream is None:
        _db.cache_avatar(player.avatarhash, player.avatarfull)

    _tid = team * 100 + player_id
    _name: sg.Text = window[f"playerNamePlate{_tid}"]
    _time: sg.Text = window[f"playerTimePlate{_tid}"]
    _ping: sg.Text = window[f"playerPingPlate{_tid}"]
    _icon: sg.Image = window[f"playerIconPlate{_tid}"]
    _combo: sg.Combo = window[f"playerAssociationCombo{_tid}"]
    _cb: sg.Checkbox = window[f"playerCheckbox{_tid}"]

    _name.update(value=player.personaname, visible=True, text_color=player.association.color)
    _time.update(value=player.game_time, visible=True)
    _ping.update(value=f"{player.ping}ms", visible=True)
    if _img_b64_stream is not None:
        _icon.update(visible=True, data=_img_b64_stream.encode('utf8'))

    # print(_img_b64_stream)
    # TODO: update icon somehow
    _combo.update(value=player.association, visible=True)
    _cb.update(visible=True, value=False)

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
    sg.theme("DarkPurple1")
    window = build_window()
    _last_update: datetime = lobby_watcher.lobby.last_update
    while True:
        event, values = window.read(timeout=5)
        if event == sg.WIN_CLOSED:
            break

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
    client_loader = TF2eLoader(_data_path)
    game_lobby = lobby.LobbyWatching(client_loader.rcon_client, client_loader.steam_client)
    game_lobby.lobby.connect_listener(client_loader.log_listener)

    with open(str(_data_path.joinpath("images/tf2b64.txt")), 'r') as h:
        TF2_LOGO_B64 = h.read()

    main(client_loader, game_lobby)
