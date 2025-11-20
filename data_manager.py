import os
import json
from typing import Any, Dict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def _file_path(name: str) -> str:
    return os.path.join(DATA_DIR, name)


def load_json(name: str, default: Any) -> Any:
    path = _file_path(name)
    if not os.path.exists(path):
        save_json(name, default)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        save_json(name, default)
        return default


def save_json(name: str, data: Any) -> None:
    path = _file_path(name)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    try:
        os.replace(tmp, path)
    except Exception:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


# Convenience wrappers -------------------------------------------------


def load_users() -> Dict[str, str]:
    # {username: password}
    return load_json("users.json", {})


def save_users(users: Dict[str, str]) -> None:
    save_json("users.json", users)


def load_settings() -> Dict[str, Any]:
    # {"theme": "Pink", "dark": False, "last_user": "kalyani"}
    return load_json("settings.json", {"theme": "Pink", "dark": False, "last_user": ""})


def save_settings(settings: Dict[str, Any]) -> None:
    save_json("settings.json", settings)
