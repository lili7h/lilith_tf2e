from src.modules.backend.g15parser.consumer import G15DumpPlayer, Team


class PlayerDump:
    """
    A container of all the relevant G15 data pertaining to a particular player.
    This player may or may not be the invoking player.
    Some values may be 0/invalid if the targeted player is not on the invoking players team.
    """
    alive: bool = None
    name: str = None
    health: int = None
    ping: int = None
    score: int = None
    deaths: int = None
    connected: bool = None
    steamid3: str = None
    ig_id: int = None
    valid: bool = None
    team: Team = None
    ammo: int = None

    def __init__(self, name: str) -> None:
        self.name = name

    def set_alive(self, val: bool) -> None:
        self.alive = val

    def set_name(self, val: str) -> None:
        self.name = val

    def set_health(self, val: int) -> None:
        self.health = val

    def set_ping(self, val: int) -> None:
        self.ping = val

    def set_score(self, val: int) -> None:
        self.score = val

    def set_deaths(self, val: int) -> None:
        self.deaths = val

    def set_connected(self, val: bool) -> None:
        self.connected = val

    def set_steamid3(self, val: str) -> None:
        self.steamid3 = val

    def set_ig_id(self, val: int) -> None:
        self.ig_id = val

    def set_valid(self, val: bool) -> None:
        self.valid = val

    def set_team(self, val: int | Team) -> None:
        if type(val) is int:
            self.team = Team(val)
        else:
            self.team = val

    def set_ammo(self, val: int) -> None:
        self.ammo = val


def int_to_team(num: int) -> Team:
    """ Convert an int (0, 1, 2, or 3) into a Team enum element. """
    return Team(num)


def get_id3_from_iAccountID(m_iAccountID: int) -> str:
    """ Convert the G15 'm_iAccountID' variable into a valid SteamID3 """
    return f"[U:1:{m_iAccountID}]"


def get_player_idx(dump: G15DumpPlayer, sid3: str = None, name: str = None, ig_id: int = None):
    """
    Given one of the optional named parameters, find the respective idx in the G15 lists.
    this can then be used to call "get_player_stats_from_idx()" to get a PlayerDump object.

    :param dump: the G15DumpPlayer object returned from parsing the `g15_dumpplayer` command output
    :param sid3: optional - the SteamID3 of the player you want the idx of
    :param name: optional - the 'personaname' or nickname of the player you want the idx of
    :param ig_id: optional - the in-game id (the first column in the output of `status`) you want the idx of.
    :return: idx of the specified player, or -1 if not found.
    """
    if sid3 is not None:
        for idx, _pl_id in enumerate(dump.get_local_player_resource_data().m_iAccountID):
            _built_sid3 = get_id3_from_iAccountID(_pl_id)
            if _built_sid3 == sid3:
                return idx

    if name is not None:
        for idx, _pl_name in enumerate(dump.get_local_player_resource_data().m_szName):
            if _pl_name == name:
                return idx

    if ig_id is not None:
        for idx, _ig_id in enumerate(dump.get_local_player_resource_data().m_iUserID):
            if _ig_id == ig_id:
                return idx

    return -1


def get_player_stats_from_idx(dump: G15DumpPlayer, player_idx: int) -> PlayerDump:
    """
    Get all the relevant data elements to a particular player (specified by G15 Idx) and populate the
    PlayerDump instance with it, before returning it.

    :param dump: the G15DumpPlayer object returned from parsing the `g15_dumpplayer` command output
    :param player_idx: the idx of the player you want the data on. Can be got using `get_player_idx`
    :return: PlayerDump instance containing all relevant data on this player.
    """
    _lp = dump.get_local_player_data()
    _pr = dump.get_local_player_resource_data()

    _pl = PlayerDump(_pr.m_szName[player_idx])
    _pl.set_ammo(_lp.m_iAmmo[player_idx])
    _pl.set_team(_pr.m_iTeam[player_idx])
    _pl.set_valid(_pr.m_bValid[player_idx])
    _pl.set_ping(_pr.m_iPing[player_idx])

    _pl.set_steamid3(get_id3_from_iAccountID(_pr.m_iAccountID[player_idx]))
    _pl.set_alive(_pr.m_bAlive[player_idx])

    _pl.set_score(_pr.m_iScore[player_idx])
    _pl.set_deaths(_pr.m_iDeaths[player_idx])
    _pl.set_health(_pr.m_iHealth[player_idx])

    _pl.set_connected(_pr.m_bConnected[player_idx])
    _pl.set_ig_id(_pr.m_iUserID[player_idx])
    return _pl


def get_player_stats_from_identifier(
        dump: G15DumpPlayer, sid3: str = None, name: str = None, ig_id: int = None
) -> PlayerDump:
    """
    Helper function to combine `get_player_idx` with `get_player_stats_from_idx`, provided an identifying trait,
    get a PlayerDump object in return.

    :param dump: the G15DumpPlayer object returned from parsing the `g15_dumpplayer` command output
    :param sid3: optional - the SteamID3 of the player you want the idx of
    :param name: optional - the 'personaname' or nickname of the player you want the idx of
    :param ig_id: optional - the in-game id (the first column in the output of `status`) you want the idx of.
    :return: PlayerDump instance containing all relevant data on this player.
    """
    _idx = get_player_idx(dump, sid3, name, ig_id)
    if _idx == -1:
        raise ValueError(f"No player idx was found with the provided identifier: {sid3}/{name}/{ig_id}")
    _pl = get_player_stats_from_idx(dump, _idx)
    return _pl
