from src.modules.tf2e.lobby import TF2Player
from src.modules.tf2e.main import TF2eLoader
from src.modules.rc.proc_reporter import is_hl2_running, get_hl2_pid
from pathlib import Path
from src.modules.tf2e import lobby
from datetime import datetime
from typing import Literal

import PySimpleGUI as sg

sg.theme("DarkPurple1")

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

t1PlayerListLayout = [
    [sg.Text("Players:", font="Any 14"), sg.Text("0", font="Any 14", key="team1PlayerCount")],
    [sg.Listbox(values=init_list, enable_events=True, expand_y=True, expand_x=True,
                select_mode="LISTBOX_SELECT_MODE_SINGLE", key='ListboxTeam1')]
]

t2PlayerListLayout = [
    [sg.Text("Players:", font="Any 14"), sg.Text("0", font="Any 14", key="team2PlayerCount")],
    [sg.Listbox(values=init_list, enable_events=True, expand_y=True, expand_x=True,
                select_mode="LISTBOX_SELECT_MODE_SINGLE", key='ListboxTeam2')]
]

t1PlayerList = sg.Frame(
    title="Team 1", element_justification="left", key="t1PlayerListFrame", layout=t1PlayerListLayout,
    expand_x=True, expand_y=True,
)

t2PlayerList = sg.Frame(
    title="Team 2", element_justification="left", key="t2PlayerListFrame", layout=t2PlayerListLayout,
    expand_x=True, expand_y=True,
)

lobbyPlayersLayout = [
    [t1PlayerList, t2PlayerList]
]

# TODO: Work on this
playerMenuListingColumn1 = sg.Column([
    [sg.Text("-undefined-", key="playerNamePlateN", font='Any 14')],
    [sg.Text("-undefined-", key="playerProfilePlateN", font='Any 12')]
])

playerMenuListing = [
    sg.Image(source=str(Path("../../../data/images/tf2.png")), subsample=32),
    playerMenuListingColumn1,
    sg.Text("-undefined-", key="playerPingPlateN", font='Any 12', text_color="green")
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

            _col1: sg.Listbox = window['ListboxTeam1']
            _col2: sg.Listbox = window['ListboxTeam2']
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

            _col1.update(values=team_players[0], set_to_index=_ti1)
            _col2.update(values=team_players[1], set_to_index=_ti2)

            _pc1.update(value=str(len(team_players[0])))
            _pc2.update(value=str(len(team_players[1])))

            _last_update = datetime.now()
            window.refresh()
        event, values = window.read(timeout=5)
        # End program if user closes window or
        # presses the OK button
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        if len(values['ListboxTeam1']):
            if not values['ListboxTeam1'][0] == "-none-":
                update_player_details(window, team=1, player=values['ListboxTeam1'][0])
                selected_players[0] = values['ListboxTeam1'][0]
        if len(values['ListboxTeam2']):
            if not values['ListboxTeam2'][0] == "-none-":
                update_player_details(window, team=2, player=values['ListboxTeam2'][0])
                selected_players[1] = values['ListboxTeam2'][0]

    loader.log_listener.end()
    globby.kill_watcher()
    window.close()


if __name__ == "__main__":
    _data_path = Path("../../../data/")
    client_loader = TF2eLoader(_data_path)
    game_lobby = lobby.LobbyWatching(client_loader.rcon_client, client_loader.steam_client)
    game_lobby.lobby.connect_listener(client_loader.log_listener)
    _window = sg.Window("SimpleLobbyViewer", layout=layout, resizable=True)

    main(client_loader, game_lobby, _window)
