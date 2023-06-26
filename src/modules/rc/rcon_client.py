from rcon.source import Client
from src.modules.rc.proc_reporter import is_hl2_running

import loguru


class RCONListener:
    rcon_ip: str = None
    rcon_port: int = None
    rcon_pword: str = None

    def __init__(
            self,
            pword: str,
            ip: str = "127.0.0.1",
            port: int = 27015
    ) -> None:
        self.rcon_ip = ip
        self.rcon_port = port
        self.rcon_pword = pword

    def spawn_client(self) -> None:
        if is_hl2_running():
            with Client(self.rcon_ip, self.rcon_port, passwd=self.rcon_pword) as h:
                loguru.logger.info(f"RCON: " + h.run("echo", "hello tf2e!").strip())
        else:
            loguru.logger.error(f"TF2 (or any hl2.exe process) is not running currently, cannot spawn an rcon client.")
            # loguru error should raise an exception already, but this line is here to satisfy linting.
            raise Exception(f"TF2 (or any hl2.exe process) is not running currently, cannot spawn an rcon client.")

    def run(self, command: str, *args) -> str:
        with Client(self.rcon_ip, self.rcon_port, passwd=self.rcon_pword) as h:
            _response = h.run(command, *args)

        return _response


class RCONHelper:
    @classmethod
    def get_lobby_data(cls, rcon_listener: RCONListener) -> str:
        _lobby = rcon_listener.run("tf_lobby_debug")
        return _lobby

    @classmethod
    def echo(cls, rcon_listener: RCONListener, message: str) -> str:
        return rcon_listener.run(message)
