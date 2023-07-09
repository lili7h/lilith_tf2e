import re


class TF2StatusBlob:
    PREFIX_LEN: int = 10
    HST_PREFIX: str = "hostname: "
    VER_PREFIX: str = "version : "
    UDP_PREFIX: str = "udp/ip  : "
    SID_PREFIX: str = "steamid : "
    ACC_PREFIX: str = "account : "
    MAP_PREFIX: str = "map     : "
    TAG_PREFIX: str = "tags    : "
    PLS_PREFIX: str = "players : "
    NUM_PLAYERS_REGEX: str = r"(players\s:\s)(\d+)\shumans,\s(\d+)\sbots\s\((\d+)\smax\)"
    EDS_PREFIX: str = "edicts  : "
    # No groups
    # list seperator example: # userid name                uniqueid            connected ping loss state
    PLAYER_LIST_SEPARATOR_REGEX: str = r"#\s+userid\s+name\s+uniqueid\s+connected\s+ping\s+loss\s+state"
    # Groups ordering:
    # 0: full str, 1: userid, 2: Quote delimited username, 3: SteamID3, 4: time in server, 5: ping, 6: loss, 7: state
    PLAYER_LIST_LINE_REGEX: str = r'(#\s+(\d{2,4})\s+(".+")\s+(\[U:\d:\d+\])\s+(\d?:?\d{2}:\d{2})\s+(\d{1,3})\s+(\d{1,3})\s+(\S+))'

    status_hst: str = None
    status_ver: str = None
    status_udp: str = None
    status_sid: str = None
    status_acc: str = None
    status_map: str = None
    status_tag: str = None
    status_pls: str = None
    status_eds: str = None

    munched_player_sep: bool = None

    players: list[re.Match] = None
    num_players: int = None
    num_bots: int = None
    max_players: int = None

    full_munch: bool = None
    excess_junk: list[str] = None

    def __init__(self):
        self.munched_player_sep = False
        self.full_munch = False
        self.players = []
        self.excess_junk = []

    def munch(self, next_line: str) -> bool:
        """
        Munches the next line of terminal output, returning true if no more `status` data is expected
        (i.e. all headers munched, expected number of players munched)
        :param next_line: the next line of terminal output
        :return: true if no more `status` data expected
        """
        if not next_line.strip():
            return self.full_munch
        if not self.status_hst and next_line.startswith(self.HST_PREFIX):
            self.status_hst = next_line[self.PREFIX_LEN:]
        elif not self.status_ver and next_line.startswith(self.VER_PREFIX):
            self.status_ver = next_line[self.PREFIX_LEN:]
        elif not self.status_udp and next_line.startswith(self.UDP_PREFIX):
            self.status_udp = next_line[self.PREFIX_LEN:]
        elif not self.status_sid and next_line.startswith(self.SID_PREFIX):
            self.status_sid = next_line[self.PREFIX_LEN:]
        elif not self.status_acc and next_line.startswith(self.ACC_PREFIX):
            self.status_acc = next_line[self.PREFIX_LEN:]
        elif not self.status_map and next_line.startswith(self.MAP_PREFIX):
            self.status_map = next_line[self.PREFIX_LEN:]
        elif not self.status_tag and next_line.startswith(self.TAG_PREFIX):
            self.status_tag = next_line[self.PREFIX_LEN:]
        elif not self.status_pls and next_line.startswith(self.PLS_PREFIX):
            self.status_pls = next_line[self.PREFIX_LEN:]
            _match = re.search(self.NUM_PLAYERS_REGEX, next_line)
            if _match is None:
                self.excess_junk.append(next_line)
            else:
                _groups = _match.groups()
                self.num_players = _groups[1]
                self.num_bots = _groups[2]
                self.max_players = _groups[3]
        elif not self.status_eds and next_line.startswith(self.EDS_PREFIX):
            self.status_eds = next_line[self.PREFIX_LEN:]
        elif not self.munched_player_sep and \
                re.search(self.PLAYER_LIST_SEPARATOR_REGEX, next_line) is not None:
            self.munched_player_sep = True
        elif next_line.startswith("#"):
            _match = re.search(self.PLAYER_LIST_LINE_REGEX, next_line)
            if _match is not None:
                self.players.append(_match)
                if self.num_players is not None and len(self.players) > int(self.num_players):
                    print(f"Extra player match on: {next_line}. Found {len(self.players)} / {int(self.num_players)}")
                    raise ValueError("Matched more players than expected. What is happening?")
            else:
                self.excess_junk.append(next_line)
        else:
            self.excess_junk.append(next_line)

        if str(len(self.players)) == self.num_players and \
                self.munched_player_sep and \
                None not in [
                    self.status_hst,
                    self.status_ver,
                    self.status_udp,
                    self.status_sid,
                    self.status_acc,
                    self.status_map,
                    self.status_tag,
                    self.status_eds
                ]:
            self.full_munch = True

        return self.full_munch
