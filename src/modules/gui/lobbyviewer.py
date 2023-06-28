from src.modules.tf2e.lobby import TF2Player, DummyTF2Player
from src.modules.tf2e.main import TF2eLoader
from src.modules.rc.proc_reporter import is_hl2_running, get_hl2_pid
from pathlib import Path
from src.modules.tf2e import lobby
from datetime import datetime
from typing import Literal

import PySimpleGUI as sg

sg.theme("DarkPurple1")


def create_detail_labels_column() -> sg.Column:
    return sg.Column(
        layout=[[sg.Text("Name:")], [sg.Text("SteamID3:")], [sg.Text("SteamID64:")], [sg.Text("Profile:")],
                [sg.Text("Location:")], [sg.Text("Created:")], [sg.Text("VAC:")]]
    )


def get_detail_data_column_keys(team: Literal[1, 2]) -> list[str]:
    _t = str(team)
    return [
        f'nameTeam{_t}Player',
        f'sid3Team{_t}Player',
        f'sid64Team{_t}Player',
        f'purlTeam{_t}Player',
        f'locTeam{_t}Player',
        f'createdTeam{_t}Player',
        f'vacTeam{_t}Player',
    ]


def set_detail_data_column_style(window: sg.Window) -> None:
    _key_names = get_detail_data_column_keys(1) + get_detail_data_column_keys(2)
    for _k in _key_names:
        window[_k].Widget.config(readonlybackground=sg.theme_background_color())
        window[_k].Widget.config(borderwidth=0)


def create_detail_data_column(team: Literal[1, 2]) -> sg.Column:
    _key_names = get_detail_data_column_keys(team)
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


def create_detail_data_frame(team: Literal[1, 2]) -> sg.Frame:
    return sg.Frame(
        layout=[
            [create_detail_labels_column(), create_detail_data_column(team)]
        ],
        title=f"Team {team}",
        element_justification="left",
        key=f"t{team}PlayerListFrame",
        expand_x=True, expand_y=True,
    )

def create_player_tile(tile_id: int, player: TF2Player | DummyTF2Player) -> sg.Frame:
    # TODO: Player tiles may have to be changed
    player_tile_text_plate = sg.Column([
        [sg.Text(player.personaname, key=f"playerNamePlate{tile_id}", font='Any 14')],
        [
            sg.Text(player.game_time, key=f"playerTimePlate{tile_id}", font='Any 12'),
            sg.Text(player.ping, key=f"playerPingPlate{tile_id", font='Any 12')
        ]
    ])

    # TODO: call async image download if player.pfp_cached == False, leave image as default TF2 logo and set cached to
    #       true. When player updates occur, we will check for if the cached image exists locally on the drive yet,
    #       and update the image source then.
    player_tile_plate = [
        [
            sg.Image(
                source=str(Path("../../../data/images/tf2.png")), subsample=32, key=f"playerIconPlate{tile_id}"
            ),
            player_tile_text_plate,
            sg.Combo(
                readonly=True, key=f"playerAssociationCombo{tile_id}", font="Any 14",
                values=TF2Player.possible_associations, default_value=player.association, enable_events=True
            )
        ]
    ]

    _frame = sg.Frame(layout=player_tile_plate, title=f"{player.loccountrycode}", key=f"playerTileFrame{tile_id}",
                      title_location=sg.TITLE_LOCATION_BOTTOM_RIGHT, relief=sg.RELIEF_RIDGE)

    return _frame

def create_player_tiles(team: Literal[1, 2]) -> sg.Column:
    _team_frames = []
    for i in range(16):
        _dummy = DummyTF2Player(team*100 + i)
        _frame = create_player_tile(team*100 + i, _dummy)
        _frame.update(visible=False)
        _team_frames.append(_frame)
    return sg.Column(layout=[
        _team_frames
    ], key=f"playerTilesColumn{team}")


def spawn_player_tiles() -> tuple[sg.Column, sg.Column]:
    return create_player_tiles(1), create_player_tiles(2)


def player_listing_frame() -> sg.Frame:
    _t1_players, _t2_players = spawn_player_tiles()
    return sg.Frame(
        title="Players in Lobby",
        layout=[[_t1_players, _t2_players]],
        expand_x=True, expand_y=True,
        size=(800, 800),
        key="playerListingFrame"
    )


def spawn_player_detail_frames() -> tuple[sg.Frame, sg.Frame]:
    return create_detail_data_frame(1), create_detail_data_frame(2)

def player_detail_frame() -> sg.Frame:
    _t1_detail_data, _t2_detail_data = spawn_player_detail_frames()
    return sg.Frame(
        title="Advanced Details",
        layout=[[_t1_detail_data, _t2_detail_data]],
        expand_x=True, expand_y=True,
        size=(800, 400),
        key="playerDetailsFrame"
    )

def update_player_tile(window: sg.Window, player_id: int, team: Literal[1,2], player: TF2Player) -> None:
    _tid = team*100 + player_id
    _name: sg.Text = window[f"playerNamePlate{_tid}"]
    _time: sg.Text = window[f"playerTimePlate{_tid}"]
    _ping: sg.Text = window[f"playerPingPlate{_tid}"]
    _icon: sg.Image = window[f"playerIconPlate{_tid}"]
    _combo: sg.Combo = window[f"playerAssociationCombo{_tid}"]

    _name.update(value=player.personaname)
    _time.update(value=player.game_time)
    _ping.update(value=f"{player.ping}ms")
    # TODO: update icon somehow
    _combo.update(value=player.association)

    window[f"playerTileFrame{_tid}"].update(visible=True)


def about_and_status() -> sg.Frame:
    # TODO: clean up how we generate the about and status frames.
    headerDataColumn = sg.Column([
        [sg.Text("Simple Lobby Viewer v0.1.0a", justification="c", font="Any 20")],
        [sg.Text("Created by Lilith", font="Any 16", text_color="white")],
        [sg.Text("(C) 2023, MIT License", font="Any 10", text_color="white")],
    ])

    headerLayout = [
        [sg.Image(source=str(Path("../../../data/images/lilith.png")), subsample=16), headerDataColumn]
    ]

    headerFrame = sg.Frame(title="About", layout=headerLayout)

    TF2StatusColumn = sg.Column([
        [sg.Text("TF2 is %status%", text_color="red", key="tf2statuselem")],
        [sg.Text("PID:"), sg.Text("-none-", key="tf2pidkey")],
        [sg.Text("Steam Con:"), sg.Text("-none-", key="steamstatuskey", text_color="red")]
    ])

    statusLayout = [
        [sg.Image(source=str(Path("../../../data/images/tf2.png")), subsample=16), TF2StatusColumn]
    ]

    statusFrame = sg.Frame(title="Status", layout=statusLayout)

    return sg.Frame(
        title="",
        layout=[[headerFrame, statusFrame]],
        key="headerFrame"
    )

def build() -> sg.Column:
    _app_status: sg.Frame = about_and_status()
    _player_listing: sg.Frame = player_listing_frame()
    _player_details: sg.Frame = player_detail_frame()

    main_display: sg.Column = sg.Column(
        layout=[
            [_app_status],
            [_player_listing],
            [_player_details],
        ],
        key="mainDisplay"
    )
    return main_display




playerFrameColumnLayoutLabels1 = [
    [sg.Text("Name:")], [sg.Text("SteamID3:")], [sg.Text("SteamID64:")], [sg.Text("Profile:")], [sg.Text("Location:")],
    [sg.Text("Created:")], [sg.Text("VAC:")],
]

# Cannot reuse Elements in a window at any point
# So we have to do this gross jank just to instantiate new Text elements with the same labels.
playerFrameColumnLayoutLabels2 = [
    [sg.Text("Name:")], [sg.Text("SteamID3:")], [sg.Text("SteamID64:")], [sg.Text("Profile:")], [sg.Text("Location:")],
    [sg.Text("Created:")], [sg.Text("VAC:")],
]

t1PlayerFrameColumnLayoutData = [
    [sg.InputText("(null)", key='nameTeam1Player', use_readonly_for_disable=True, disabled=True)],
    [sg.InputText("(null)", key='sid3Team1Player', use_readonly_for_disable=True, disabled=True)],
    [sg.InputText("(null)", key='sid64Team1Player', use_readonly_for_disable=True, disabled=True)],
    [sg.InputText("(null)", key='purlTeam1Player', use_readonly_for_disable=True, disabled=True)],
    [sg.InputText("(null)", key='locTeam1Player', use_readonly_for_disable=True, disabled=True)],
    [sg.InputText("(null)", key='createdTeam1Player', use_readonly_for_disable=True, disabled=True)],
    [sg.InputText("(null)", key='vacTeam1Player', use_readonly_for_disable=True, disabled=True)],
]

t2PlayerFrameColumnLayoutData = [
    [sg.InputText("(null)", key='nameTeam2Player', use_readonly_for_disable=True, disabled=True)],
    [sg.InputText("(null)", key='sid3Team2Player', use_readonly_for_disable=True, disabled=True)],
    [sg.InputText("(null)", key='sid64Team2Player', use_readonly_for_disable=True, disabled=True)],
    [sg.InputText("(null)", key='purlTeam2Player', use_readonly_for_disable=True, disabled=True)],
    [sg.InputText("(null)", key='locTeam2Player', use_readonly_for_disable=True, disabled=True)],
    [sg.InputText("(null)", key='createdTeam2Player', use_readonly_for_disable=True, disabled=True)],
    [sg.InputText("(null)", key='vacTeam2Player', use_readonly_for_disable=True, disabled=True)],
]

t1PlayerFrameLayout = [
    [sg.Column(layout=playerFrameColumnLayoutLabels1), sg.Column(layout=t1PlayerFrameColumnLayoutData)]
]

t2PlayerFrameLayout = [
    [sg.Column(layout=playerFrameColumnLayoutLabels2), sg.Column(layout=t2PlayerFrameColumnLayoutData)]
]

t1PlayerDetails = sg.Frame(
    title="Team 1 Player", element_justification="left", key="t1PlayerFrame", layout=t1PlayerFrameLayout,
    expand_x=True, expand_y=True,
)

t2PlayerDetails = sg.Frame(
    title="Team 2 Player", element_justification="left", key="t2PlayerFrame", layout=t2PlayerFrameLayout,
    expand_x=True, expand_y=True,
)

init_list = ["-none-"] * 12

t1PlayerList = []
t2PlayerList = []

t1PlayerListLayout = [
    [sg.Text("Players:", font="Any 14"), sg.Text("0", font="Any 14", key="team1PlayerCount")],
    [sg.Column(layout=t1PlayerList)],
    # [sg.Listbox(values=init_list, enable_events=True, expand_y=True, expand_x=True,
    #             select_mode="LISTBOX_SELECT_MODE_SINGLE", key='ListboxTeam1')]
]

t2PlayerListLayout = [
    [sg.Text("Players:", font="Any 14"), sg.Text("0", font="Any 14", key="team2PlayerCount")],
    [sg.Column(layout=t2PlayerList)],
    # [sg.Listbox(values=init_list, enable_events=True, expand_y=True, expand_x=True,
    #             select_mode="LISTBOX_SELECT_MODE_SINGLE", key='ListboxTeam2')]
]

t1PlayerList_ = sg.Frame(
    title="Team 1", element_justification="left", key="t1PlayerListFrame", layout=t1PlayerListLayout,
    expand_x=True, expand_y=True,
)

t2PlayerList_ = sg.Frame(
    title="Team 2", element_justification="left", key="t2PlayerListFrame", layout=t2PlayerListLayout,
    expand_x=True, expand_y=True,
)

lobbyPlayersLayout = [
    [t1PlayerList_, t2PlayerList_]
]

playerListingFrame = sg.Frame(
    title="Players in Lobby",
    layout=lobbyPlayersLayout,
    expand_x=True, expand_y=True,
    size=(800, 400)
)

headerDataColumn = sg.Column([
    [sg.Text("Simple Lobby Viewer v0.1.0a", justification="c", font="Any 18")],
    [sg.Text("Created by Lilith", font="Any 14", text_color="white")],
    [sg.Text("(C) 2023, MIT License", font="Any 10", text_color="white")],
])

headerLayout = [
    [sg.Image(source=str(Path("../../../data/images/lilith.png")), subsample=16), headerDataColumn]
]

headerFrame = sg.Frame(title="About", layout=headerLayout)

TF2StatusColumn = sg.Column([
    [sg.Text("TF2 is %status%", text_color="red", key="tf2statuselem")],
    [sg.Text("PID:"), sg.Text("-none-", key="tf2pidkey")],
    [sg.Text("Steam Con:"), sg.Text("-none-", key="steamstatuskey", text_color="red")]
])

statusLayout = [
    [sg.Image(source=str(Path("../../../data/images/tf2.png")), subsample=16), TF2StatusColumn]
]

statusFrame = sg.Frame(title="Status", layout=statusLayout)

sublayout = [
    [headerFrame, statusFrame],
    [playerListingFrame],
    [sg.HorizontalSeparator()],
    [sg.Stretch(), sg.Text('Player Details', font='Any 14'), sg.Stretch()],
    [t1PlayerDetails, t2PlayerDetails],
    [sg.HorizontalSeparator()],
    [sg.Button('Exit')],
]

layout = [[sg.Frame(title="Simple Lobby Viewer", layout=sublayout, expand_x=True, expand_y=True, size=(950, 1000))]]


def update_player_details(window: sg.Window, team: Literal[1, 2], player: TF2Player) -> None:
    _ident = f"Team{team}Player"
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


# Create the window
def main(loader: TF2eLoader, globby: lobby.LobbyWatching, window: sg.Window):
    # Create an event loop
    _last_update: datetime = datetime.now()
    selected_players: list[TF2Player] = [None, None]
    sg.theme("DarkPurple1")
    while True:
        _time_diff = datetime.now() - _last_update
        if _time_diff.seconds > 3:
            team_players: tuple[list[TF2Player], list[TF2Player]] = ([], [])
            with globby.lobby.lobby_lock:
                for _pl in globby.lobby.players:
                    if _pl.lobby_team == "TF_GC_TEAM_DEFENDERS":
                        team_players[1].append(_pl)
                    elif _pl.lobby_team == "TF_GC_TEAM_INVADERS":
                        team_players[0].append(_pl)

            # _col1: sg.Listbox = window['ListboxTeam1']
            # _col2: sg.Listbox = window['ListboxTeam2']
            _pc1 = window["team1PlayerCount"]
            _pc2 = window["team2PlayerCount"]
            _tf2_status: sg.Text = window["tf2statuselem"]
            _tf2_pid: sg.Text = window["tf2pidkey"]
            _steam_status: sg.Text = window["steamstatuskey"]

            if is_hl2_running:
                _tf2_status.update(value="TF2 is running!", text_color="green")
            else:
                _tf2_status.update(value="TF2 is closed :(", text_color="red")

            _tf2_pid.update(value=str(get_hl2_pid()))

            if loader.steam_client is not None:
                _steam_status.update(value="online!", text_color="green")
            else:
                _steam_status.update(value="offline :(", text_color="red")

            try:
                _ti1 = team_players[0].index(selected_players[0]) if selected_players[0] is not None else None
            except ValueError:
                _ti1 = None
            try:
                _ti2 = team_players[1].index(selected_players[1]) if selected_players[1] is not None else None
            except ValueError:
                _ti2 = None

            t1PlayerList = []
            t2PlayerList = []
            for _t1player in team_players[0]:
                t1PlayerList.append(create_player_tile(_t1player))
            for _t2player in team_players[1]:
                t2PlayerList.append(create_player_tile(_t2player))

            # _col1.update(values=team_players[0], set_to_index=_ti1)
            # _col2.update(values=team_players[1], set_to_index=_ti2)

            _pc1.update(value=str(len(team_players[0])))
            _pc2.update(value=str(len(team_players[1])))

            _last_update = datetime.now()
            window.refresh()
        event, values = window.read(timeout=5)
        # End program if user closes window or
        # presses the OK button
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        # if len(values['ListboxTeam1']):
        #     if not values['ListboxTeam1'][0] == "-none-":
        #         update_player_details(window, team=1, player=values['ListboxTeam1'][0])
        #         selected_players[0] = values['ListboxTeam1'][0]
        # if len(values['ListboxTeam2']):
        #     if not values['ListboxTeam2'][0] == "-none-":
        #         update_player_details(window, team=2, player=values['ListboxTeam2'][0])
        #         selected_players[1] = values['ListboxTeam2'][0]

    loader.log_listener.end()
    globby.kill_watcher()
    window.close()


def main2(loader: TF2eLoader, globby: lobby.LobbyWatching):
    sg.theme("DarkPurple1")
    _main_disp = build()
    _window = sg.Window("SimpleLobbyViewer v0.2.0a", layout=[[_main_disp]], resizable=True)
    _last_update: datetime = datetime.now()
    # TODO: implement live loop, including player tile updates.
    # TODO: implement player icon caching using the icon hash as an efficiency measure
    # TODO: clean up how we dummy define the player frames.




if __name__ == "__main__":
    _data_path = Path("../../../data/")
    client_loader = TF2eLoader(_data_path)
    game_lobby = lobby.LobbyWatching(client_loader.rcon_client, client_loader.steam_client)
    game_lobby.lobby.connect_listener(client_loader.log_listener)

    main2(client_loader, game_lobby)
    # _window = sg.Window("SimpleLobbyViewer", layout=layout, resizable=True)
    # main(client_loader, game_lobby, _window)
