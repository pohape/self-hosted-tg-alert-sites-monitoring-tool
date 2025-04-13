import json
import os
import platform
from typing import Protocol, runtime_checkable, cast

import yaml


def load_yaml_or_exit(file_name: str):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)

    if not os.path.isfile(path):
        exit(f"{path} not found")

    with open(path, 'r') as file:
        return yaml.safe_load(file)


@runtime_checkable
class Writer(Protocol):
    def write(self, __s: str) -> int: ...


def get_cache_path():
    if platform.system() == 'Windows':
        base_dir = os.environ.get('TEMP') or os.environ.get('TMP') or 'C:\\Temp'
    else:
        base_dir = '/tmp'

    return os.path.join(base_dir, 'self-hosted-tg-alert-sites-monitoring-tool.json')


def load_cache():
    path = get_cache_path()

    if not os.path.isfile(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)


def save_cache(cache: dict) -> None:
    with open(get_cache_path(), 'w', encoding='utf-8') as f:
        writer = cast(Writer, f)
        json.dump(cache, writer, indent=2)
