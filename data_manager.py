# data_manager.py
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def _file_path(name):
    return os.path.join(DATA_DIR, name)


def load_json(name, default):
    """
    Load JSON from data/<name>. If missing or invalid, write default and return it.
    """
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


def save_json(name, data):
    """
    Write JSON to data/<name>.
    """
    path = _file_path(name)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    try:
        os.replace(tmp, path)
    except Exception:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)



def load_users():
    # {username: password}
    return load_json("users.json", {})


def save_users(users):
    save_json("users.json", users)


def load_settings():
    # {"theme": "Pink", "dark": False, "last_user": ""}
    return load_json("settings.json", {"theme": "Pink", "dark": False, "last_user": ""})


def save_settings(settings):
    save_json("settings.json", settings)
