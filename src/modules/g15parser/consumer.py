from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
from typing import Union, Literal
from pathlib import Path

import loguru

from src.modules.rc.FragClient import FragClient
import numpy as np
import struct
import re

FLOAT_MAX = struct.unpack('>f', b'\x7f\x7f\xff\xff')


class Vector3D:
    """
    Dummy vector class that uses np.arrays for the pure fact that np implemented
    vector arithmetic and operations, which may or may not be useful at any point.
    """
    def __init__(self, vec: list):
        self.vec = np.array(vec)

    def get(self):
        return self.vec


_jd = dict[str, Union[int, float, bool, str, Vector3D, bytes]]


class Team(Enum):
    """
    TF2 actually has 4 distinct teams.
    We only ever really play as red or blu, so 2 or 3.
    """
    Unconnected = 0
    Spectator = 1
    Red = 2
    Blue = 3


class InternalVarMShared:
    """
    m_Shared is a struct that is mapped across several classes/structs in the g15 dump, and thus we store them
    externally to the data classes themselves to allow cross-class referencing
    """
    m_nPlayerState: int = None
    m_nPlayerCond: int = None
    m_flCloakMeter: float = None
    m_flRageMeter: float = None
    m_flNextRageEarnTime: float = None
    m_bRageDraining: bool = None
    m_flEnergyDrinkMeter: float = None
    m_flInvisChangeCompleteTime: float = None
    m_flHypeMeter: float = None
    m_nDisguiseTeam: int = None
    m_flChargeMeter: float = None
    m_nDisguiseClass: int = None
    m_bJumping: bool = None
    m_nDisguiseSkinOverride: int = None
    m_iAirDash: int = None
    m_nMaskClass: int = None
    m_nAirDucked: int = None
    m_nDesiredDisguiseTeam: int = None
    m_flDuckTimer: float = None
    m_nDesiredDisguiseClass: int = None
    m_bLastDisguisedAsOwnTeam: bool = None
    m_bFeignDeathReady: bool = None
    m_nPlayerCondEx: int = None
    m_nPlayerCondEx2: int = None
    m_flDisguiseCompleteTime: float = None
    m_nPlayerCondEx3: int = None
    m_bHasPasstimeBall: bool = None
    m_nPlayerCondEx4: int = None
    m_bIsTargetedForPasstimePass: bool = None
    m_askForBallTime: float = None
    m_flItemChargeMeter: list[float] = None

    def __init__(self) -> None:
        self.m_flItemChargeMeter = [0.0]*10


class InternalVarMLocal:
    """
    m_Local is a shared struct that contains data on the local player and events
    """
    m_nStepside: int = None
    m_bPrevForceLocalPlayerDraw: bool = None
    m_iHideHUD: int = None
    m_vecPunchAngle: Vector3D = None
    m_vecPunchAngleVel: Vector3D = None
    m_bDrawViewmodel: bool = None
    m_bAllowAutoMovement: bool = None
    m_bWearingSuit: bool = None
    m_bDucked: bool = None
    m_bPoisoned: bool = None
    m_bDucking: bool = None
    m_bForceLocalPlayerDraw: bool = None
    m_bInDuckJump: bool = None
    m_flDucktime: float = None
    m_flDuckJumpTime: float = None
    m_flJumpTime: float = None
    m_flFallVelocity: float = None
    m_nOldButtons: int = None
    m_flOldForwardMove: float = None
    m_flStepSize: float = None
    m_flFOVRate: float = None


class InternalVarMCollision:
    """
    m_Collision is a common struct between multiple classes, and details the relevant components of the collision
    properties of something. Technically each data class should have its own instance of this, but since we don't
    actually care about collision properties, we just have every class point at the same one. This can be changed
    later if necessary.
    """
    m_vecMinsPreScaled: Vector3D = None
    m_vecMaxsPreScaled: Vector3D = None
    m_vecMaxs: Vector3D = None
    m_vecMins: Vector3D = None
    m_nSolidType: None = None
    m_triggerBloat: None = None
    m_usSolidFlags: int = None
    m_bUniformTriggerBloat: bool = None


class InternalVar:
    """
    Data class containing references to shared common structs
    """
    m_Shared = InternalVarMShared()
    m_Local = InternalVarMLocal()
    m_Collision = InternalVarMCollision()


class pl:
    """
    this is a bit of a stub, but the way it appears in the dump output, `pl` is probably a player struct, but may or may
    not be an artifact of porting from half life 1, and thus has mostly irrelevant data in it that doesn't pertain to
    multiplayer. Either that or they don't like revealing the data in here...
    """
    deadflag: bool = None


class IntVarLocalPlayer:
    """
    Local player data, most useful thing in here is probably `m_iTeamNum`, but this is duplicated across other
    data classes anyway. Notably, the current ammo in mag value of _every player in the server_ is recorded in here.
    """
    m_Shared = InternalVar.m_Shared
    m_Local = InternalVar.m_Local
    m_nSequence: int = None
    m_flPlaybackRate: float = None
    m_flCycle: float = None
    m_flEncodedController: list[float] = None
    m_nSkin: int = None
    m_nBody: int = None
    m_nNewSequenceParity: int = None
    m_nResetEventsParity: int = None
    m_flInspectTime: float = None
    m_nMuzzleFlashParity: None = None
    m_flHelpmeButtonPressTime: float = None
    m_flTauntYaw: float = None
    m_flCurrentTauntMoveSpeed: float = None
    m_flVehicleReverseTime: float = FLOAT_MAX,
    pl: pl = pl
    m_iFOV: int = None
    m_flFOVTime: float = None
    m_iFOVStart: int = None
    m_flMaxspeed: float = None
    m_iHealth: int = None
    m_iBonusProgress: int = None
    m_iBonusChallenge: int = None
    m_fOnTarget: bool = None
    m_nNextThinkTick: int = None
    m_vecBaseVelocity: Vector3D = None
    m_lifeState: None = None
    m_nButtons: int = None
    m_nWaterLevel: None = None
    m_flWaterJumpTime: float = None
    m_nImpulse: int = None
    m_flPhysics: int = None
    m_flStepSoundTime: float = None
    m_szAnimExtensiongl: None = None
    m_flSwimSoundTime: float = None
    m_afButtonLast: int = None
    m_vecLadderNormal: Vector3D = None
    m_afButtonPressed: int = None
    m_iAmmo: list[int] = None
    m_afButtonReleased: int = None
    m_nTickBase: int = None
    m_surfaceFriction: int = None
    m_flNextAttack: float = None
    m_nPrevSequence: int = None
    m_Collision = InternalVar.m_Collision
    m_MoveCollide: None = None
    m_MoveType: bytes = None
    m_vecAbsVelocity: Vector3D = None
    m_vecVelocity: Vector3D = None
    m_nRenderMode: None = None
    m_nRenderFX: None = None
    m_fFlags: int = None
    m_vecViewOffset: Vector3D = None
    m_nModelIndex: int = None
    m_flFriction: float = None
    m_iTeamNum: int = None
    m_vecNetworkOrigin: Vector3D = None
    m_vecAbsOrigin: Vector3D = None
    m_angNetworkAngles: Vector3D = None
    m_angAbsRotation: Vector3D = None
    m_vecOrigin: Vector3D = None
    m_angRotation: Vector3D = None
    m_vecAngVelocity: Vector3D = None
    m_nWaterType: None = None
    m_bDormant: bool = None
    m_flGravity: float = None
    m_iEFlags: int = None
    m_flProxyRandomValue: float = None

    def __init__(self):
        self.m_flEncodedController: list[float] = [0.0]*4
        self.m_iAmmo: list[int] = [0]*32


class IntVarLocalTeam:
    """
    Contains the name of the team the local player is on. Annoyingly this is presented as either the `m_szTeamnameBlue`
    field or the `m_szTeamnameRed` field existing (i.e. not None), perhaps artifacts of having multiple team colors
    planned? either way, it just makes checking the team name slightly more annoying.
    """
    m_szTeamnameBlue: None = None
    m_szTeamnameRed: None = None
    m_iScore: int = None
    m_iRoundsWon: int = None
    m_iPing: int = None
    m_iDeaths: int = None
    m_iPacketloss: int = None
    m_iTeamNum: int = None
    m_Collision = InternalVar.m_Collision
    m_MoveType: None = None
    m_MoveCollide: None = None
    m_vecAbsVelocity: Vector3D = None
    m_fFlags: int = None
    m_vecVelocity: Vector3D = None
    m_vecViewOffset: Vector3D = None
    m_nRenderMode: None = None
    m_nModelIndex: int = None
    m_nRenderFX: None = None
    m_flFriction: float = None
    m_angNetworkAngles: Vector3D = None
    m_vecNetworkOrigin: Vector3D = None
    m_vecAbsOrigin: Vector3D = None
    m_angAbsRotation: Vector3D = None
    m_vecOrigin: Vector3D = None
    m_vecAngVelocity: Vector3D = None
    m_angRotation: Vector3D = None
    m_bDormant: bool = None
    m_nWaterLevel: None = None
    m_vecBaseVelocity: Vector3D = None
    m_nWaterType: None = None
    m_iEFlags: int = None
    m_flGravity: float = None
    m_flProxyRandomValue: float = None
    m_szName: list[str] = None

    def __init__(self):
        self.m_szName: list[str] = [""]*1


class IntVarPlayerResource:
    """
    A big compendium of resources related to _all_ players in the server. This includes:
    - the nick names (i.e. 'personaname') of every player in the server
    - the ping of every player in the server
    - the score of every player in the server
    - the number of deaths of every player in the server
    - the connected status of every player in the server
    - the team number of every player in the server
    - the alive flag of every player in the server
    - the SteamID3 of every player in the server
    - the in game ID of every player in the server
    - the current health value of every player on your team
    - the 'validity' of every player slot (probably determines what the scoreboard shows)
    """
    m_szName: list[str] = None
    m_iPing: list[int] = None
    m_iScore: list[int] = None
    m_iDeaths: list[int] = None
    m_bConnected: list[bool] = None
    m_iTeam: list[Team] = None
    m_bAlive: list[bool] = None
    m_iHealth: list[int] = None
    m_iAccountID: list[int] = None
    m_iUserID: list[int] = None
    m_bValid: list[bool] = None
    m_Collision = InternalVar.m_Collision
    m_MoveCollide: None = None
    m_MoveType: None = None
    m_vecAbsVelocity: Vector3D = None
    m_nRenderMode: None = None
    m_vecVelocity: Vector3D = None
    m_nRenderFX: None = None
    m_vecViewOffset: Vector3D = None
    m_fFlags: int = None
    m_nModelIndex: int = None
    m_flFriction: float = None
    m_iTeamNum: int = None
    m_vecNetworkOrigin: Vector3D = None
    m_angNetworkAngles: Vector3D = None
    m_vecAbsOrigin: Vector3D = None
    m_vecOrigin: Vector3D = None
    m_angAbsRotation: Vector3D = None
    m_angRotation: Vector3D = None
    m_nWaterLevel: None = None
    m_nWaterType: None = None
    m_vecAngVelocity: Vector3D= None
    m_bDormant: bool = None
    m_vecBaseVelocity: Vector3D = None
    m_bLowered: bool = None
    m_iEFlags: int = None
    m_iReloadMode: int = None
    m_flGravity: float = None
    m_bReloadedThroughAnimEvent: bool = None
    m_flProxyRandomValue: float = None
    m_bDisguiseWeapon: bool = None

    def __init__(self):
        self.m_szName: list[str] = [""] * 34
        self.m_iPing: list[int] = [0] * 34
        self.m_iScore: list[int] = [0] * 34
        self.m_iDeaths: list[int] = [0] * 34
        self.m_bConnected: list[bool] = [False] * 34
        self.m_iTeam: list[Team] = [Team.Unconnected] * 34
        self.m_bAlive: list[bool] = [False] * 34
        self.m_iHealth: list[int] = [0] * 34
        self.m_iAccountID: list[int] = [0] * 34
        self.m_iUserID: list[int] = [0] * 34
        self.m_bValid: list[bool] = [False] * 34


class IntVarLocalPlayerWeapon:
    """
    Who knows if much of this is useful? It contains local data on the local players crit seed and such, which may
    prove useful to some.
    """
    m_flLastCritCheckTime: float = None
    m_flReloadPriorNextFire: float = None
    m_flLastFireTime: float = None
    m_bCurrentAttackIsCrit: bool = None
    m_iCurrentSeed: int = None
    m_flEnergy: float = None
    m_flEffectBarRegenTime: float = None
    m_bBeingRepurposedForTaunt: bool = None
    m_nNextThinkTick: int = None
    m_iState: int = None
    m_iViewModelIndex: int = None
    m_iWorldModelIndex: int = None
    m_flNextPrimaryAttack: float = None
    m_flNextSecondaryAttack: float = None
    m_flTimeWeaponIdle: float = None
    m_iPrimaryAmmoType: int = None
    m_iSecondaryAmmoType: int = None
    m_nViewModelIndex: int = None
    m_iClip1: int = None
    m_iClip2: int = None
    m_bInReload: bool = None
    m_bFireOnEmpty: bool = None
    m_flNextEmptySoundTime: float = None
    m_bFiringWholeClip: bool = None
    m_Activity: int = None
    m_fFireDuration: float = None
    m_bFiresUnderwater: bool = None
    m_iszName: int = None
    m_bAltFiresUnderwater: bool = None
    m_fMinRange1: float = None
    m_fMinRange2: float = None
    m_fMaxRange1: float = None
    m_fMaxRange2: float = None
    m_bReloadsSingly: bool = None
    m_bRemoveable: bool = None
    m_iPrimaryAmmoCount: int = None
    m_iSecondaryAmmoCount: int = None
    m_nSkin: int = None
    m_flPlaybackRate: float = None
    m_nBody: int = None
    m_flCycle: float = None
    m_nSequence: int = None
    m_flEncodedController: list[float] = None
    m_nPrevSequence: int = None
    m_nNewSequenceParity: int = None
    m_nResetEventsParity: int = None
    m_nMuzzleFlashParity: bytes = None
    m_Collision = InternalVar.m_Collision
    m_MoveType: None = None
    m_MoveCollide: None = None
    m_vecAbsVelocity: Vector3D = None
    m_vecVelocity: Vector3D = None
    m_nRenderMode: None = None
    m_nRenderFX: None = None
    m_fFlags: int = None
    m_vecViewOffset: Vector3D = None
    m_nModelIndex: int = None
    m_flFriction: float = None
    m_iTeamNum: int = None
    m_vecNetworkOrigin: Vector3D = None
    m_angNetworkAngles: Vector3D = None
    m_vecAbsOrigin: Vector3D = None
    m_angAbsRotation: Vector3D = None
    m_vecOrigin: Vector3D = None
    m_angRotation: Vector3D = None
    m_nWaterLevel: None = None
    m_nWaterType: None = None
    m_vecAngVelocity: Vector3D = None
    m_bDormant: bool = None
    m_vecBaseVelocity: Vector3D = None
    m_iEFlags: int = None
    m_flGravity: float = None
    m_flProxyRandomValue: float = None

    def __init__(self):
        self.m_flEncodedController: list[float] = [0.0]*4


class G15Stream:
    """
    A useful metaclass that turns the list of strings generated from splitting the output of `g15_dumpplayer` on
    newlines into a generator with specifiable start and end sections. This allows us to use the section delimiters
    embedded within the command output such as "(localplayerweapon)" as flags to segment the data stream into iterable
    chunks all within the one variable.
    """
    def __init__(self, stream: list[str], start: str, until: str) -> None:
        self.stream = stream
        self.start = start
        self.idx = self.stream.index(self.start)
        self.until = until

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        try:
            _elem = ""
            while not _elem.strip():
                _elem = self.stream[self.idx]
                if _elem == self.until:
                    raise StopIteration
                self.idx += 1
            return _elem
        except IndexError:
            raise StopIteration


class G15DumpPlayer:
    """
    A data class that parses the output of the `g15_dumpplayer` command into the 4 relevant data classes.

    The G15 data is extracted via RCON de-fragged packets, and fed in here. The constructor performs the
    simple iterative data parsing to apply the values to the data classes.
    """
    _LocalPlayer: IntVarLocalPlayer = None
    _LocalTeam: IntVarLocalTeam = None
    _PlayerResource: IntVarPlayerResource = None
    _LocalPlayerWeapon: IntVarLocalPlayerWeapon = None
    localplayer: str = "(localplayer)"
    localteam: str = "(localteam)"
    playerresource: str = "(playerresource)"
    localplayerweapon: str = "(localplayerweapon)"
    end: str = "Other replacements:"

    def debug_print_localplayer(self) -> None:
        print(self._LocalPlayer.__dict__)

    @staticmethod
    def _fix_values(values: list[str]) -> None:
        if len(values) < 3:
            if ord(values[0][len(values[0]) - 1:]) < 20:
                values.append("bytes")
                values.append(values[0][len(values[0]) - 1:])
            else:
                values.append("none")
                values.append("(none)")

    @staticmethod
    def _parse_value(value_str: str, value_type: str) -> bytes | str | int | float | bool | Vector3D:
        parsed_val = None
        if value_type == "vector":
            parsed_val = Vector3D(value_str[1:len(value_str) - 1].split())
        elif value_type == "integer" or value_type == "short":
            parsed_val = int(value_str[1:len(value_str) - 1])
        elif value_type == "bool":
            parsed_val = value_str[1:len(value_str) - 1] == "true"
        elif value_type == "float":
            parsed_val = float(value_str[1:len(value_str) - 1])
        elif value_type == "none":
            parsed_val = None
        elif value_type == "bytes":
            parsed_val = bytes(value_str, encoding="utf8")
        return parsed_val

    @staticmethod
    def _set_attribute(primary_target, sub_target, var_name, parsed_val) -> None:
        _array_regex = r"\[(\d+)\]"
        _match = re.search(_array_regex, var_name)
        if _match:
            if sub_target is not None:
                _idx = int(_match.groups()[0])
                _target: list = getattr(sub_target, var_name.split(".")[1].split("[")[0])
                _target[_idx] = parsed_val
            else:
                _idx = int(_match.groups()[0])
                _target: list = getattr(primary_target, var_name.split("[")[0])
                _target[_idx] = parsed_val
        else:
            if sub_target is not None:
                setattr(sub_target, var_name.split(".")[1], parsed_val)
            else:
                setattr(primary_target, var_name, parsed_val)

    def __init__(self, command_stream: str) -> None:
        """
        This is incredibly gross as a function

        It's got a lot of repeated code that could be (and probably will be later)
        abstracted into sub functions. But it works and it's quick.

        Parse the output of `g15_dumpplayer` into data classes.
        :param command_stream: the stream of str of the command
        """
        self._LocalPlayer = IntVarLocalPlayer()
        self._LocalTeam = IntVarLocalTeam()
        self._PlayerResource = IntVarPlayerResource()
        self._LocalPlayerWeapon = IntVarLocalPlayerWeapon()
        _start = datetime.now()

        if not command_stream.split():
            loguru.logger.warning(f"Not in lobby, not parsing G15.")
            return

        _g15_dumpplayer_stream = command_stream.split("\n")

        # TODO: Attempt to refactor the 4 distinct for loops into one to reduce code duplication

        # (localplayer) data
        for i in G15Stream(_g15_dumpplayer_stream, self.localplayer, self.localteam):
            values = i.split()
            self._fix_values(values)

            varName, varType, currentValue = values[0], values[1], values[2]

            # parse value
            parsed_val = self._parse_value(currentValue, varType)

            sub_target = getattr(self._LocalPlayer, varName.split(".")[0]) if "." in varName else None
            self._set_attribute(self._LocalPlayer, sub_target, varName, parsed_val)

        # print(f"Stored {len(self._LocalPlayer.__dict__.keys())} values in {self._LocalPlayer.__class__.__name__}")

        for i in G15Stream(_g15_dumpplayer_stream, self.localteam, self.playerresource):
            values = i.split()
            self._fix_values(values)

            varName, varType, currentValue = values[0], values[1], values[2]

            # parse value
            parsed_val = self._parse_value(currentValue, varType)

            sub_target = getattr(self._LocalTeam, varName.split(".")[0]) if "." in varName else None
            self._set_attribute(self._LocalTeam, sub_target, varName, parsed_val)

        # print(f"Stored {len(self._LocalTeam.__dict__.keys())} values in {self._LocalTeam.__class__.__name__}")

        for i in G15Stream(_g15_dumpplayer_stream, self.playerresource, self.localplayerweapon):
            values = i.split()
            self._fix_values(values)

            varName, varType, currentValue = values[0], values[1], values[2]

            # parse value
            parsed_val = self._parse_value(currentValue, varType)

            sub_target = getattr(self._PlayerResource, varName.split(".")[0]) if "." in varName else None
            self._set_attribute(self._PlayerResource, sub_target, varName, parsed_val)

        # print(f"Stored {len(self._PlayerResource.__dict__.keys())} values in {self._PlayerResource.__class__.__name__}")

        for i in G15Stream(_g15_dumpplayer_stream, self.localplayerweapon, self.end):
            values = i.split()
            self._fix_values(values)

            varName, varType, currentValue = values[0], values[1], values[2]

            # parse value
            parsed_val = self._parse_value(currentValue, varType)

            sub_target = getattr(self._LocalPlayerWeapon, varName.split(".")[0]) if "." in varName else None
            self._set_attribute(self._LocalPlayerWeapon, sub_target, varName, parsed_val)

        # print(f"Stored {len(self._LocalPlayerWeapon.__dict__.keys())} values in {self._LocalPlayerWeapon.__class__.__name__}")

    def get_local_player_data(self) -> IntVarLocalPlayer:
        return self._LocalPlayer

    def get_local_team_data(self) -> IntVarLocalTeam:
        return self._LocalTeam

    def get_local_player_resource_data(self) -> IntVarPlayerResource:
        return self._PlayerResource

    def get_local_player_weapon_data(self) -> IntVarLocalPlayerWeapon:
        return self._LocalPlayerWeapon


def do_g15(rcon_conf: tuple[str, int, str]) -> G15DumpPlayer:
    """
    Given the rcon configuration params, invoke a custom FragClient instance to invoke the 'g15_dumpplayer' command
    and sequentially read and concatenate the response (fragmented) packets. Then this response is passed to
    G15DumpPlayer and a parsed G15DumpPlayer instance is returned.

    :param rcon_conf: a tuple containing the: rcon_ip, rcon_port, rcon_password
    :return: The constructed G15DumpPlayer instance.
    """
    with FragClient(rcon_conf[0], rcon_conf[1], passwd=rcon_conf[2]) as h:
        resp = h.frag_run("g15_dumpplayer")
    _inst = G15DumpPlayer(resp)
    return _inst

def main():
    # rcon_ip = "127.0.0.1"
    # rcon_port = 27015
    # rcon_pword = "lilith_is_hot"
    # with FragClient(rcon_ip, rcon_port, passwd=rcon_pword) as h:
    #     resp = h.frag_run("g15_dumpplayer")
    with open(Path("../../../data/logs/g15_dumpplayer.log"), 'r') as h:
        resp = h.read()

    _inst = G15DumpPlayer(resp)
    # rcon_conf = ("127.0.0.1", 27015, "lilith_is_hot")
    # _inst = do_g15(rcon_conf)


if __name__ == "__main__":
    main()

