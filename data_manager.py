# data_manager.py
import os
import json
from typing import Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def _file_path(name: str) -> str:
    # name should be like "todos.json"
    return os.path.join(DATA_DIR, name)


def load_json(name: str, default: Any):
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
        # Corrupted file -> replace with default
        save_json(name, default)
        return default


def save_json(name: str, data: Any):
    """
    Write JSON to data/<name> atomically-ish (simple).
    """
    path = _file_path(name)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    try:
        os.replace(tmp, path)
    except Exception:
        # fallback
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
