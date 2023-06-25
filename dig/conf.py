from pathlib import Path
import yaml
import os
import loguru


def load_config(config: Path) -> dict:
    if not os.path.exists(config):
        loguru.logger.error(f"config.yml file could not be found at {config}, has it moved?")

    with open(config, 'r', encoding='utf8') as h:
        _configs = yaml.safe_load(h)

    return _configs
