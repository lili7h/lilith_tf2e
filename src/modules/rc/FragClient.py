from rcon.source import Client
from socket import SOCK_STREAM
from rcon.exceptions import SessionTimeout, WrongPassword
from rcon.source.proto import Packet, Type, random_request_id
from functools import partial


class FragClient(Client, socket_type=SOCK_STREAM):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def frag_communicate(self, packet: Packet) -> Packet:
        """Send and receive a packet."""
        self.send(packet)
        _dummy_pack = make_command_frag()
        self.send(_dummy_pack)
        _total_packet: Packet | None = None
        while True:
            _pack = self.read()
            if _pack.type == Type.SERVERDATA_RESPONSE_VALUE:
                if _pack.id == _dummy_pack.id or _pack.payload == b'\x00\x00\x00\x01\x00\x00\x00\x00':
                    break
                else:
                    if _total_packet is None:
                        _total_packet = _pack
                    else:
                        _total_packet += _pack

        return _total_packet

    def frag_run(self, command: str, *args: str, encoding: str = 'utf-8') -> str:
        """Run a command."""
        request = Packet.make_command(command, *args, encoding=encoding)
        response = self.frag_communicate(request)

        if response.id != request.id:
            raise SessionTimeout()

        return response.payload.decode(encoding)


def make_command_frag() -> Packet:
    return Packet(
        random_request_id(), Type.SERVERDATA_RESPONSE_VALUE,
        b''
    )
