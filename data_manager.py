# data_manager.py
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def _file_path(name):
    """
    Build an absolute path inside the data/ folder.
    """
    return os.path.join(DATA_DIR, name)


def load_json(name, default):
    """
    Load JSON from data/<name>.

    - If file doesn't exist → create it with default and return default.
    - If file is corrupted → overwrite with default and return default.
    """
    path = _file_path(name)

    if not os.path.exists(path):
        save_json(name, default)
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # corrupted / unreadable
        save_json(name, default)
        return default


def save_json(name, data):
    """
    Write JSON to data/<name> using a temp file swap so it's harder to corrupt.
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


# -------------------------------------------------------------------
# USERS
# -------------------------------------------------------------------

def load_users():
    """
    Users are stored as:
    {
        "username1": "password1",
        "username2": "password2",
        ...
    }
    """
    return load_json("users.json", {})


def save_users(users):
    save_json("users.json", users)


# -------------------------------------------------------------------
# SETTINGS (theme, dark mode, last user, font)
# -------------------------------------------------------------------

def load_settings():
    """
    Settings structure:
    {
        "theme": "Pink",
        "dark": False,
        "last_user": "",
        "font": "Avenir"
    }
    """
    default = {
        "theme": "Pink",
        "dark": False,
        "last_user": "",
        "font": "Avenir",
    }
    settings = load_json("settings.json", default)

    for k, v in default.items():
        if k not in settings:
            settings[k] = v

    return settings


def save_settings(settings):
    save_json("settings.json", settings)


# -------------------------------------------------------------------
# Bootstrap all JSON files once
# -------------------------------------------------------------------

def ensure_all_defaults():
    """
    Call this once in main.py to guarantee that all JSON files exist.
    It won't overwrite anything non-empty.
    """
    # To-dos: list of {"text", "priority", "done"}
    load_json("todos.json", [])

    # Flashcards: list of {"front", "back", "known"}
    load_json("flashcards.json", [])

    # Notes:
    # {
    #   "folders": {
    #     "Subject": {
    #       "complete": false,
    #       "units": {
    #         "Unit 1": {"content": "..." },
    #         ...
    #       }
    #     }
    #   }
    # }
    load_json("notes.json", {"folders": {}})

    # Resources:
    # {
    #   "subjects": {
    #     "Subject": {
    #       "units": {
    #         "Unit 1": ["link1", "link2"]
    #       }
    #     }
    #   }
    # }
    load_json("resources.json", {"subjects": {}})

    # Schedule: {"yyyy-MM-dd": ["entry1", "entry2"], "__all__": [...] (legacy)}
    load_json("schedule.json", {})

    # Ensure users/settings exist
    load_users()
    load_settings()
