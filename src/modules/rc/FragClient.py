import loguru
from rcon.source import Client
from socket import SOCK_STREAM
from rcon.exceptions import SessionTimeout, WrongPassword
from rcon.source.proto import Packet, Type, random_request_id
from functools import partial


class FragClient(Client, socket_type=SOCK_STREAM):
    """
    This class is identical to the base rcon.source.Client it extends, except it implements a useful
    frag_communicate method for implementing the advice given here:
    https://developer.valvesoftware.com/wiki/Source_RCON_Protocol#Multiple-packet_Responses

    It uses an empty SERVERDATA_RESPONSE_VALUE packet as a command to create a 'delimiting packet' the suffixes
    the fragmented data being returned from the initial command, thus allowing you to determine when the fragmentation
    has been fully collected.

    Source RCON is a TCP socket server, thus packets are always sent in-order, and with ECC.

    TODO: check if this leaves a dangling packet in the recv buffer, resulting in future messages failing.
    """

    def __init__(self, *args, **kwargs):
        """
        Arguments: rcon_ip, rcon_port, passwd=rcon_pword
        default ip should be 127.0.0.1 (not 0.0.0.0), and default port is 27015
        Downside of using *args and **kwargs is that you lose parameter hinting in your IDE.
        """
        super().__init__(*args, **kwargs)

    def frag_communicate(self, packet: Packet) -> Packet:
        """Send and receive a fragmented packet using some helpful packet delimiting and packet defragmentation."""
        self.send(packet)
        _dummy_pack = make_command_frag()
        self.send(_dummy_pack)
        _total_packet: Packet | None = None
        while True:
            try:
                _pack = self.read()
            except ValueError:
                loguru.logger.warning(f"Read invalid packet from server...")
                continue
            if _pack.type == Type.SERVERDATA_RESPONSE_VALUE:
                if _pack.id == _dummy_pack.id or _pack.payload == b'\x00\x00\x00\x01\x00\x00\x00\x00':
                    break
                else:
                    if _total_packet is None:
                        _total_packet = _pack
                    elif _pack.id == packet.id:
                        _total_packet += _pack

        return _total_packet

    def frag_run(self, command: str, *args: str, encoding: str = 'utf-8') -> str:
        """Run a command. Invokes frag_communicate rather than the usual communicate."""
        request = Packet.make_command(command, *args, encoding=encoding)
        response = self.frag_communicate(request)

        if response.id != request.id:
            raise SessionTimeout()

        return response.payload.decode(encoding, errors='ignore')


def make_command_frag() -> Packet:
    """
    An empty packet that is of type SERVERDATA_RESPONSE_VALUE to trigger the RCON source server to reply in kind.
    :return: A dummy packet
    """
    return Packet(
        random_request_id(), Type.SERVERDATA_RESPONSE_VALUE,
        b''
    )
