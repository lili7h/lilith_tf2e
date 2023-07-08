import datetime
import os
import pathlib
from pathlib import Path
from PIL import Image
from io import BytesIO
from threading import Lock

import base64
import requests
import loguru
import shutil


class CacheSingletonManager(type):
    """
    Singleton metaclass for managing the singleton meta type. Do not attempt to directly instantiate,
    reference or otherwise use this class. Its function is autonomous.
    """
    _instances = {}

    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class AvCache(metaclass=CacheSingletonManager):
    cache_path: Path = None
    indexes: dict[str, Path] = None

    def __init__(self, cache_path: Path) -> None:
        if self.cache_path is None:
            self.cache_path = cache_path
            self.convert_jpegs()
        if self.indexes is None:
            self.indexes = {}
            for _img in self.cache_path.glob("*.png"):
                self.indexes[_img.name.split(".")[0]] = _img

    def convert_jpegs(self) -> None:
        to_remove = []
        for _img in self.cache_path.glob("*.jpg"):
            im = Image.open(str(_img))
            im.save(f'{self.cache_path}/{_img.name.split(".")[0]}.png')
            to_remove.append(_img)

        for _p in to_remove:
            os.remove(str(_p))

    def cache_image(self, img_hash: str, img_url: str) -> bool:
        if not (img_url.startswith("https://avatars.akamai.steamstatic.com/")
                or img_url.startswith("https://avatars.steamstatic.com/")):
            loguru.logger.error(f"Attempted to fetch avatar image from outside of Steams CDN. "
                                f"Aborting for safety. {img_url}")
            return False
        try:
            _img_path = self.indexes[img_hash]
            if _img_path is not None:
                return True
        except KeyError:
            pass

        response = requests.get(img_url)
        image_bytes = response.content
        with open(f'{self.cache_path}/{img_hash}.jpg', 'wb') as h:
            h.write(image_bytes)

        im = Image.open(f'{self.cache_path}/{img_hash}.jpg')
        im.save(f'{self.cache_path}/{img_hash}.png')

        os.remove(f'{self.cache_path}/{img_hash}.jpg')

        self.indexes[img_hash] = self.cache_path.joinpath(f'{img_hash}.png')

        return True

    def get_image(self, img_hash) -> Path | None:
        try:
            _img_path = self.indexes[img_hash]
            return _img_path
        except KeyError:
            return None

    def check_tf2_small_in_cache(self, data_path: Path) -> None:
        try:
            _img_path = self.indexes["tf2small"]
            return
        except KeyError:
            pass

        if os.path.exists(f'{self.cache_path}/tf2small.png'):
            self.indexes["tf2small"] = Path(f'{self.cache_path}/tf2small.png')
            return
        else:
            shutil.copy(data_path.joinpath("images/tf2small.png"), self.cache_path)
            self.indexes["tf2small"] = Path(f'{self.cache_path}/tf2small.png')


def main():
    avatar_hash = "427ef7d5f8ad7b21678f69bc8afc95786cf38fe6"
    avatar_url = "https://avatars.akamai.steamstatic.com/427ef7d5f8ad7b21678f69bc8afc95786cf38fe6_full.jpg"
    cache_path = Path('../../../data/cache/avatars/')
    _inst = AvCache(cache_path)
    cached = _inst.cache_image(avatar_hash, avatar_url)

    if cached:
        print("Succesfully cached image.")

    _img_path = _inst.get_image(avatar_hash)
    if _img_path:
        print(f"Image located at {_img_path}")


if __name__ == "__main__":
    main()