import json
import os
from typing import Protocol, runtime_checkable, cast

import yaml

CACHE_FILE_NAME = 'cache.json'


def load_yaml_or_exit(file_name: str):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)

    if not os.path.isfile(path):
        exit(f"{path} not found")

    with open(path, 'r') as file:
        return yaml.safe_load(file)


@runtime_checkable
class Writer(Protocol):
    def write(self, __s: str) -> int: ...


def get_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), CACHE_FILE_NAME)


def load_cache():
    path = get_path()

    if not os.path.isfile(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)


def save_cache(cache: dict) -> None:
    with open(get_path(), 'w', encoding='utf-8') as f:
        writer = cast(Writer, f)
        json.dump(cache, writer, indent=2)
