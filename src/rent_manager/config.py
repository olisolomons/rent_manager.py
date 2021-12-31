from dataclasses import dataclass
from pathlib import Path

import appdirs

import dataclass_json

rent_manager_dirs = appdirs.AppDirs('RentManager')
config_file = Path(rent_manager_dirs.user_data_dir) / 'config.json'


@dataclass
class RentManagerConfig:
    file_chooser_dir: str = None


def load() -> RentManagerConfig:
    if config_file.exists():
        with config_file.open() as f:
            return dataclass_json.load(RentManagerConfig, f)
    else:
        return RentManagerConfig()


def save(config: RentManagerConfig) -> None:
    if not config_file.parent.exists():
        config_file.parent.mkdir()

    with config_file.open('w') as f:
        dataclass_json.dump(config, f)
