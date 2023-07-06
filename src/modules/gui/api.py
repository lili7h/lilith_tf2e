from typing import Self, Any
from abc import ABC, abstractmethod

import loguru
import json
import requests


class Payload(ABC):
    def build(self) -> dict:
        _dict = {}
        for _k in self.__dict__:
            if _k.startswith("pl_"):
                _dict[_k[3:]] = self.__dict__[_k]

        return _dict

    def build_json(self) -> str:
        return json.dumps(self.build(), indent=2)


class UserPayload(Payload):
    def add_user(self, *args) -> Self:
        """
        Add a specified user to the payload

        :param kwargs:
        :return: self for object chaining
        """
        for _d in args:
            _k = _d.keys()[0]
            if getattr(self, f"pl_{_k}", None) is not None:
                loguru.logger.error(f"Key {_k} already in user payload: {self.__dict__}.")
            else:
                setattr(self, f"pl_{_k}", _d[_k])
        return self


    def add_user_data(self, steam_id_64: str, tags: list[str] = None, custom_data: dict = None) -> Self:
        """

        :param steam_id_64: the steam_id_64 of the player you want to modify the stored payload data of
        :param tags: tags to update the player data with
        :param custom_data: custom data to update the players customData block with
        :return: self for object chaining
        """
        _user = getattr(self, f"pl_{steam_id_64}", None)
        if _user is None:
            loguru.logger.error(f"Player {steam_id_64} not in paylaod data: {self.__dict__}")

        _user["tags"] = _user["tags"] + tags  # concat lists
        _user["customData"] = _user["customData"] | custom_data  # dict union

        return self

class PrefPayload(Payload):
    pl_internal: dict = None
    pl_external: dict = None

    def __init__(self) -> None:
        self.pl_internal = {}
        self.pl_external = {}

    def add_intern_pref(self, **kwargs) -> Self:
        """
        Add a specified user preference to the "internal" object key in the payload

        :return: self for function chaining
        """
        for _k in kwargs:
            if _k in self.pl_internal:
                loguru.logger.error(f"Key {_k} already in internal: {self.pl_internal}.")
            self.pl_internal[_k] = kwargs[_k]

        return self

    def add_extern_pref(self, **kwargs) -> Self:
        """
        Add a specified user preference to the "external" object key in the payload

        :return: self for function chaining
        """
        for _k in kwargs:
            if _k in self.pl_external:
                loguru.logger.error(f"Key {_k} already in extern: {self.pl_external}.")
            self.pl_external[_k] = kwargs[_k]

        return self


class MACAPI:
    base_url: str = None
    api_ver: str = "v1"

    def __init__(self, base: str) -> None:
        self.base_url = base

    def set_api_version(self, version: int) -> None:
        self.api_ver = f"v{version}"

    def get_game(self, *, api_version: int = None) -> dict:
        _local_api_ver = self.api_ver if api_version is None else f"v{api_version}"
        _endpoint = f"{self.base_url}/mac/game/{_local_api_ver}"

        response = requests.get(_endpoint)
        return json.loads(response.json())

    def get_user(self, steam_id_64: str, *, api_version: int = None) -> dict:
        _local_api_ver = self.api_ver if api_version is None else f"v{api_version}"
        _endpoint = f"{self.base_url}/mac/user/{_local_api_ver}/{steam_id_64}"

        response = requests.get(_endpoint)
        return json.loads(response.json())

    def post_user(self, user_payload: dict, *, api_version: int = None) -> dict:
        _local_api_ver = self.api_ver if api_version is None else f"v{api_version}"
        _endpoint = f"{self.base_url}/mac/user/{_local_api_ver}"

        response = requests.post(_endpoint, data=user_payload)
        return json.loads(response.json())

    def get_pref(self, *, api_version: int = None) -> dict:
        _local_api_ver = self.api_ver if api_version is None else f"v{api_version}"
        _endpoint = f"{self.base_url}/mac/pref/{_local_api_ver}"

        response = requests.get(_endpoint)
        return json.loads(response.json())

    def post_pref(self, pref_payload: dict, *, api_version: int = None) -> dict:
        _local_api_ver = self.api_ver if api_version is None else f"v{api_version}"
        _endpoint = f"{self.base_url}/mac/pref/{_local_api_ver}"

        response = requests.post(_endpoint, data=pref_payload)
        return json.loads(response.json())

    def get_event(self, *, api_version: int = None) -> dict:
        """
        The events endpoint will be a HTTP Event Stream (continual socket) from the backend, so you probably
        want to multithread this or asynchio it.
        
        :param api_version: a function-local override for the api endpoint version.
        :return: the first event payload to return
        """
        _local_api_ver = self.api_ver if api_version is None else f"v{api_version}"
        _endpoint = f"{self.base_url}/mac/events/{_local_api_ver}"

        response = requests.get(_endpoint)
        return json.loads(response.json())


if __name__ == "__main__":
    print(
        PrefPayload()
        .add_intern_pref(autokick_enabled=True)
        .add_intern_pref(autokick_interval=60)
        .add_extern_pref(xyz="Foo bar")
        .build_json()
    )
