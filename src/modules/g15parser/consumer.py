from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
from typing import Union, Literal
from pathlib import Path
from src.modules.rc.FragClient import FragClient
import numpy as np
import struct
import re

FLOAT_MAX = struct.unpack('>f', b'\x7f\x7f\xff\xff')


class Vector3D:
    def __init__(self, vec: list):
        self.vec = np.array(vec)

    def get(self):
        return self.vec


_jd = dict[str, Union[int, float, bool, str, Vector3D, bytes]]


class Team(Enum):
    Unconnected = 0
    Spectator = 1
    Red = 2
    Blue = 3


class InternalVarMShared:
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
    m_vecMinsPreScaled: Vector3D = None
    m_vecMaxsPreScaled: Vector3D = None
    m_vecMaxs: Vector3D = None
    m_vecMins: Vector3D = None
    m_nSolidType: None = None
    m_triggerBloat: None = None
    m_usSolidFlags: int = None
    m_bUniformTriggerBloat: bool = None


class InternalVar:
    m_Shared = InternalVarMShared()
    m_Local = InternalVarMLocal()
    m_Collision = InternalVarMCollision()


class pl:
    deadflag: bool = None


class IntVarLocalPlayer:
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
            _elem = self.stream[self.idx]
            if _elem == self.until:
                raise StopIteration
            self.idx += 1
            return _elem
        except IndexError:
            raise StopIteration


class G15DumpPlayer:
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

    def __init__(self, command_stream: str) -> None:
        """
        This is incredibly gross as a function

        Its got a lot of repeated code that could be (and probably will be later)
        abstracted into sub functions. But it works and its quick.

        Parse the output of `g15_dumpplayer` into data classes.
        :param command_stream: the stream of str of the command
        """
        self._LocalPlayer = IntVarLocalPlayer()
        self._LocalTeam = IntVarLocalTeam()
        self._PlayerResource = IntVarPlayerResource()
        self._LocalPlayerWeapon = IntVarLocalPlayerWeapon()
        _start = datetime.now()

        _g15_dumpplayer_stream = command_stream.split("\n")

        # (localplayer) data
        for i in G15Stream(_g15_dumpplayer_stream, self.localplayer, self.localteam):
            if not i.strip():
                continue
            values = i.split()
            if len(values) < 3:
                if ord(values[0][len(values[0])-1:]) < 20:
                    values.append("bytes")
                    values.append(values[0][len(values[0])-1:])
                else:
                    values.append("none")
                    values.append("(none)")
            varName, varType, currentValue = values[0], values[1], values[2]
            # parse value
            parsed_val = None
            if varType == "vector":
                parsed_val = Vector3D(currentValue[1:len(currentValue)-1].split())
            elif varType == "integer" or varType == "short":
                parsed_val = int(currentValue[1:len(currentValue)-1])
            elif varType == "bool":
                parsed_val = currentValue[1:len(currentValue)-1] == "true"
            elif varType == "float":
                parsed_val = float(currentValue[1:len(currentValue)-1])
            elif varType == "none":
                parsed_val = None
            elif varType == "bytes":
                parsed_val = bytes(currentValue, encoding="utf8")

            sub_target = None
            if "." in varName:
                sub_target = getattr(self._LocalPlayer, varName.split(".")[0])

            _array_regex = r"\[(\d+)\]"
            _match = re.search(_array_regex, varName)
            if _match:
                if sub_target is not None:
                    _idx = int(_match.groups()[0])
                    _target: list = getattr(sub_target, varName.split(".")[1].split("[")[0])
                    _target[_idx] = parsed_val
                else:
                    _idx = int(_match.groups()[0])
                    _target: list = getattr(self._LocalPlayer, varName.split("[")[0])
                    _target[_idx] = parsed_val
            else:
                if sub_target is not None:
                    setattr(sub_target, varName.split(".")[1], parsed_val)
                else:
                    setattr(self._LocalPlayer, varName, parsed_val)

        print(f"Stored {len(self._LocalPlayer.__dict__.keys())} values in {self._LocalPlayer.__class__.__name__}")

        for i in G15Stream(_g15_dumpplayer_stream, self.localteam, self.playerresource):
            if not i.strip():
                continue
            values = i.split()
            if len(values) < 3:
                if ord(values[0][len(values[0])-1:]) < 20:
                    values.append("bytes")
                    values.append(values[0][len(values[0])-1:])
                else:
                    values.append("none")
                    values.append("(none)")
            varName, varType, currentValue = values[0], values[1], values[2]
            # parse value
            parsed_val = None
            if varType == "vector":
                parsed_val = Vector3D(currentValue[1:len(currentValue)-1].split())
            elif varType == "integer" or varType == "short":
                parsed_val = int(currentValue[1:len(currentValue)-1])
            elif varType == "bool":
                parsed_val = currentValue[1:len(currentValue)-1] == "true"
            elif varType == "float":
                parsed_val = float(currentValue[1:len(currentValue)-1])
            elif varType == "none":
                parsed_val = None
            elif varType == "bytes":
                parsed_val = bytes(currentValue, encoding="utf8")

            sub_target = None
            if "." in varName:
                sub_target = getattr(self._LocalTeam, varName.split(".")[0])

            _array_regex = r"\[(\d+)\]"
            _match = re.search(_array_regex, varName)
            if _match:
                if sub_target is not None:
                    _idx = int(_match.groups()[0])
                    _target: list = getattr(sub_target, varName.split(".")[1].split("[")[0])
                    _target[_idx] = parsed_val
                else:
                    _idx = int(_match.groups()[0])
                    _target: list = getattr(self._LocalTeam, varName.split("[")[0])
                    _target[_idx] = parsed_val
            else:
                if sub_target is not None:
                    setattr(sub_target, varName.split(".")[1], parsed_val)
                else:
                    setattr(self._LocalTeam, varName, parsed_val)

        print(f"Stored {len(self._LocalTeam.__dict__.keys())} values in {self._LocalTeam.__class__.__name__}")

        for i in G15Stream(_g15_dumpplayer_stream, self.playerresource, self.localplayerweapon):
            if not i.strip():
                continue
            values = i.split()
            if len(values) < 3:
                if ord(values[0][len(values[0])-1:]) < 20:
                    values.append("bytes")
                    values.append(values[0][len(values[0])-1:])
                else:
                    values.append("none")
                    values.append("(none)")
            varName, varType, currentValue = values[0], values[1], values[2]
            # parse value
            parsed_val = None
            if varType == "vector":
                parsed_val = Vector3D(currentValue[1:len(currentValue)-1].split())
            elif varType == "integer" or varType == "short":
                parsed_val = int(currentValue[1:len(currentValue)-1])
            elif varType == "bool":
                parsed_val = currentValue[1:len(currentValue)-1] == "true"
            elif varType == "float":
                parsed_val = float(currentValue[1:len(currentValue)-1])
            elif varType == "none":
                parsed_val = None
            elif varType == "bytes":
                parsed_val = bytes(currentValue, encoding="utf8")

            sub_target = None
            if "." in varName:
                sub_target = getattr(self._PlayerResource, varName.split(".")[0])

            _array_regex = r"\[(\d+)\]"
            _match = re.search(_array_regex, varName)
            if _match:
                if sub_target is not None:
                    _idx = int(_match.groups()[0])
                    _target: list = getattr(sub_target, varName.split(".")[1].split("[")[0])
                    _target[_idx] = parsed_val
                else:
                    _idx = int(_match.groups()[0])
                    _target: list = getattr(self._PlayerResource, varName.split("[")[0])
                    _target[_idx] = parsed_val
            else:
                if sub_target is not None:
                    setattr(sub_target, varName.split(".")[1], parsed_val)
                else:
                    setattr(self._PlayerResource, varName, parsed_val)

        print(f"Stored {len(self._PlayerResource.__dict__.keys())} values in {self._PlayerResource.__class__.__name__}")

        for i in G15Stream(_g15_dumpplayer_stream, self.localplayerweapon, self.end):
            if not i.strip():
                continue
            values = i.split()
            if len(values) < 3:
                if ord(values[0][len(values[0])-1:]) < 20:
                    values.append("bytes")
                    values.append(values[0][len(values[0])-1:])
                else:
                    values.append("none")
                    values.append("(none)")
            varName, varType, currentValue = values[0], values[1], values[2]
            # parse value
            parsed_val = None
            if varType == "vector":
                parsed_val = Vector3D(currentValue[1:len(currentValue)-1].split())
            elif varType == "integer" or varType == "short":
                parsed_val = int(currentValue[1:len(currentValue)-1])
            elif varType == "bool":
                parsed_val = currentValue[1:len(currentValue)-1] == "true"
            elif varType == "float":
                parsed_val = float(currentValue[1:len(currentValue)-1])
            elif varType == "none":
                parsed_val = None
            elif varType == "bytes":
                parsed_val = bytes(currentValue, encoding="utf8")

            sub_target = None
            if "." in varName:
                sub_target = getattr(self._PlayerResource, varName.split(".")[0])

            _array_regex = r"\[(\d+)\]"
            _match = re.search(_array_regex, varName)
            if _match:
                if sub_target is not None:
                    _idx = int(_match.groups()[0])
                    _target: list = getattr(sub_target, varName.split(".")[1].split("[")[0])
                    _target[_idx] = parsed_val
                else:
                    _idx = int(_match.groups()[0])
                    _target: list = getattr(self._LocalPlayerWeapon, varName.split("[")[0])
                    _target[_idx] = parsed_val
            else:
                if sub_target is not None:
                    setattr(sub_target, varName.split(".")[1], parsed_val)
                else:
                    setattr(self._LocalPlayerWeapon, varName, parsed_val)

        print(f"Stored {len(self._LocalPlayerWeapon.__dict__.keys())} values in {self._LocalPlayerWeapon.__class__.__name__}")

    def get_local_player_data(self) -> IntVarLocalPlayer:
        return self._LocalPlayer

    def get_local_team_data(self) -> IntVarLocalTeam:
        return self._LocalTeam

    def get_local_player_resource_data(self) -> IntVarPlayerResource:
        return self._PlayerResource

    def get_local_player_weapon_data(self) -> IntVarLocalPlayerWeapon:
        return self._LocalPlayerWeapon


def do_g15(rcon_conf: tuple[str, int, str]) -> G15DumpPlayer:
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
    # with open(Path("../../../data/logs/g15_dumpplayer.log"), 'r') as h:
    #     resp = h.read()
    #
    # _inst = G15DumpPlayer(resp)
    rcon_conf = ("127.0.0.1", 27015, "lilith_is_hot")
    _inst = do_g15(rcon_conf)


if __name__ == "__main__":
    main()

