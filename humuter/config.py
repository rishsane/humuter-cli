"""Config and credential storage (~/.humuter/)."""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".humuter"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
CONFIG_FILE = CONFIG_DIR / "config.json"

API_BASE = os.environ.get("HUMUTER_API_URL", "https://platform.humuter.com")


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_credentials(token: str, user_id: str):
    ensure_config_dir()
    CREDENTIALS_FILE.write_text(json.dumps({
        "token": token,
        "user_id": user_id,
    }, indent=2))
    CREDENTIALS_FILE.chmod(0o600)


def load_credentials() -> dict | None:
    if not CREDENTIALS_FILE.exists():
        return None
    try:
        data = json.loads(CREDENTIALS_FILE.read_text())
        if data.get("token"):
            return data
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def clear_credentials():
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()


def get_token() -> str | None:
    creds = load_credentials()
    return creds["token"] if creds else None


def save_config(key: str, value: str):
    ensure_config_dir()
    config = {}
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            pass
    config[key] = value
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except json.JSONDecodeError:
        return {}
