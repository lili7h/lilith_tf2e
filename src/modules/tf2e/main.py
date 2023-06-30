# Packaged/bespoke modules
import sys
import time

import src.modules.rc.rcon_client as rcc
import src.modules.listener.path_listener as l2  # l2 is the legacy name for this listener class
import src.modules.helpers.conf as conf
import src.modules.caching.avatar_cache as avcache
import src.modules.tf2e.lobby as lobby

# PyPl/Pip/Poetry/System packages
from dotenv import load_dotenv
from pathlib import Path
from steam import Steam

import loguru
import os


class TF2eLoader:
    rcon_client: rcc.RCONListener = None
    log_listener: l2.Watchdog = None
    steam_client: Steam = None
    av_cache: avcache = None

    def __init__(self, data_path: Path):
        envs_loaded: bool = load_dotenv(dotenv_path=data_path.joinpath(".env"))
        if not envs_loaded:
            loguru.logger.error(f"Did not load any environment variables from {data_path}/.env - is it correct?")
            return  # unreachable - logger.error should abort execution
        configs: dict = conf.load_config(data_path.joinpath("config.yml"))

        loguru.logger.info(f"Initialising l2 listener (watching console.log)")
        _tf_path: Path
        try:
            _tf_path = Path(configs["tf2"]["dir"]).joinpath("tf/")
        except KeyError:
            loguru.logger.error(f"Failed to load tf2.dir from config.yml - how did this pass validation??")
            return  # unreachable - logger.error should abort execution
        self.log_listener = l2.Watchdog(_tf_path.joinpath("console.log"))
        self.log_listener.begin()
        loguru.logger.success(f"l2 listener watching...")

        loguru.logger.info(f"Initialising RCON client (tf2 must be running!)...")
        _rcon_pword: str
        _rcon_port: int = 27015
        _rcon_ip: str = "127.0.0.1"
        try:
            _rcon_dict = configs["tf2"]["rcon"]
            _rcon_pword = _rcon_dict["password"]
            if "ip" in _rcon_dict:
                loguru.logger.info(f"RCON client: found custom ip in configs, overriding defaults...")
                _rcon_ip = _rcon_dict["ip"]
            if "port" in _rcon_dict:
                loguru.logger.info(f"RCON client: found custom port in configs, overriding defaults...")
                _rcon_port = _rcon_dict["port"]
        except KeyError:
            loguru.logger.error(f"Failed to load tf2.rcon.password from config.yml - how did this pass validation??")
            return  # unreachable - logger.error should abort execution
        self.rcon_client = rcc.RCONListener(
            pword=_rcon_pword,
            ip=_rcon_ip,
            port=_rcon_port
        )
        self.rcon_client.spawn_client()
        loguru.logger.success(f"RCON client loaded...")

        loguru.logger.info(f"Initialising Steam API client (must have valid steam api key in .env!)...")
        self.steam_client = Steam(key=os.environ["STEAM_WEB_API_KEY"])
        loguru.logger.success(f"Steam API client initialised...")

        loguru.logger.info(f"Initialising the avatar cache DB...")
        self.av_cache = avcache.AvCache(data_path)
        loguru.logger.success(f"avatar cache DB client initialised...")


def main():
    _data_path = Path("../../../data/")
    client_loader = TF2eLoader(_data_path)
    game_lobby = lobby.LobbyWatching(client_loader.rcon_client, client_loader.steam_client)
    term_width = 240  # os.get_terminal_size().columns
    print("Players:")
    while True:
        time.sleep(5)
        sys.stdout.write('\r')
        sys.stdout.flush()
        for _pl in game_lobby.lobby.players:
            with game_lobby.lobby.lobby_lock:
                _num_spaces = term_width - len(_pl.personaname)
                sys.stdout.write(f"{_pl.personaname}{' ' * _num_spaces}")
                sys.stdout.flush()


if __name__ == "__main__":
    main()
