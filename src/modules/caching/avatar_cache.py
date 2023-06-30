import datetime
from pathlib import Path
from PIL import Image
from io import BytesIO
from threading import Lock

import base64
import requests
import sqlite3
import loguru

avatars_table_template = """
CREATE TABLE IF NOT EXISTS avatars (
    avhash text PRIMARY KEY,
    avdata text NOT NULL,
    cache_date text NOT NULL
);
"""

avatars_table_insert = """
INSERT INTO avatars(avhash,avdata,cache_date)
VALUES(?,?,?);
"""

avatars_table_get = """
SELECT avdata FROM avatars WHERE avhash=?
"""


class DBSingletonManager(type):
    """
    Singleton metaclass for managing the AssetLoadPhaseLogger singleton. Do not attempt to directly instantiate,
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


class AvCache(metaclass=DBSingletonManager):
    conn: sqlite3.Connection = None

    def __init__(self, data_path: Path):
        if self.conn is None:
            self._create_connection(data_path.joinpath("cache/avatars/avcache.db"))
            self._create_table()

    def _create_connection(self, db_file: Path):
        """ create a database connection to a SQLite database """
        _path = str(db_file)
        try:
            self.conn = sqlite3.connect(_path)
            loguru.logger.success(f"Connected to AvCache DB - with sqlite v{sqlite3.version}")
        except sqlite3.Error as e:
            loguru.logger.error(f"couldn't establish db conn to AvCache DB at {_path}. {e}")

    def _create_table(self):
        try:
            c = self.conn.cursor()
            c.execute(avatars_table_template)
        except sqlite3.Error as e:
            loguru.logger.error(f"Failed to create table for AvCache. {e}")

    def cache_avatar(self, avatar_hash: str, avatar_url: str) -> None:
        cur = self.conn.cursor()
        cur.execute(avatars_table_get, (avatar_hash,))
        rows = cur.fetchall()

        if rows:
            return  # already cached this avatar

        if not (avatar_url.startswith("https://avatars.akamai.steamstatic.com/")
                or avatar_url.startswith("https://avatars.steamstatic.com/")):
            loguru.logger.error(f"Attempted to fetch avatar image from outside of Steams CDN. "
                                f"Aborting for safety. {avatar_url}")
            return

        response = requests.get(avatar_url)
        image_bytes = response.content
        image_b64 = base64.b64encode(image_bytes)

        cur = self.conn.cursor()
        cur.execute(avatars_table_insert,
                    (avatar_hash, image_b64.decode('utf8'), datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")))
        self.conn.commit()

    def get_avatar(self, avatar_hash: str) -> None | str:
        cur = self.conn.cursor()
        cur.execute(avatars_table_get, (avatar_hash,))
        rows = cur.fetchall()

        for row in rows:
            return row[0]

        return None


def main():
    avatar_url = "https://avatars.akamai.steamstatic.com/427ef7d5f8ad7b21678f69bc8afc95786cf38fe6_full.jpg"
    response = requests.get(avatar_url)
    image_bytes = response.content
    image_b64 = base64.b64encode(image_bytes)

    print(image_b64.decode('utf8'))


if __name__ == "__main__":
    main()