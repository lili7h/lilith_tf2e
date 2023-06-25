import sys
import time
import os

from loguru import logger
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler, FileSystemEvent


class ConsoleListener(FileSystemEventHandler):
    def __init__(self, target: str):
        super().__init__()
        self.target: str = target
        self.target_cursor: int = 0

    def discard_existing(self, path_: str):
        with open(path_, 'r', encoding='utf8') as h:
            h.seek(self.target_cursor)
            new_data = h.read()
            self.target_cursor = h.tell()

    def on_modified(self, event: FileSystemEvent):
        super().on_modified(event)

        if not event.is_directory:
            _path = Path(event.src_path)
            _fn = _path.name
            if _fn == self.target:
                print("Target file modified.")
                if os.path.getsize(str(_path)) < self.target_cursor:
                    logger.warning(f"target file >>{_fn}<< was reset (size is less than current cursor)")
                    self.target_cursor = 0
                with open(str(_path), 'r', encoding='utf8') as h:
                    h.seek(self.target_cursor)
                    new_data = h.read()
                    self.target_cursor = h.tell()

                logger.info(f"New data found: ")
                print(new_data)


if __name__ == "__main__":
    fn = "console.log"
    path = sys.argv[1] if len(sys.argv) > 1 else 'D:\\Steam\\steamapps\\common\\Team Fortress 2\\tf'
    event_handler = ConsoleListener(fn)
    event_handler.discard_existing(path + f"\\{fn}")
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
