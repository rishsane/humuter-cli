"""HTTP client for the Humuter API."""

import httpx
from humuter.config import get_token, API_BASE


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"[{status}] {message}")


def _headers() -> dict:
    token = get_token()
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _handle(resp: httpx.Response) -> dict:
    if resp.status_code == 401:
        raise ApiError(401, "Unauthorized. Run `humuter login` first.")
    data = resp.json()
    if resp.status_code >= 400:
        raise ApiError(resp.status_code, data.get("error", "Unknown error"))
    return data


# --- Auth ---

def create_cli_session() -> dict:
    """POST /api/auth/cli/session — start device-flow login."""
    resp = httpx.post(f"{API_BASE}/api/auth/cli/session", headers=_headers(), timeout=15)
    return _handle(resp)


def poll_cli_session(session_id: str) -> dict:
    """GET /api/auth/cli/poll — check if user completed login."""
    resp = httpx.get(
        f"{API_BASE}/api/auth/cli/poll",
        params={"session": session_id},
        headers=_headers(),
        timeout=15,
    )
    return _handle(resp)


# --- Agents ---

def list_agents() -> list[dict]:
    resp = httpx.get(f"{API_BASE}/api/agents", headers=_headers(), timeout=15)
    data = _handle(resp)
    return data.get("agents", [])


def get_agent(agent_id: str) -> dict:
    resp = httpx.get(f"{API_BASE}/api/agents/{agent_id}", headers=_headers(), timeout=15)
    data = _handle(resp)
    return data.get("agent", data)


def create_agent(payload: dict) -> dict:
    resp = httpx.post(f"{API_BASE}/api/agents", headers=_headers(), json=payload, timeout=30)
    return _handle(resp)


def update_agent(agent_id: str, payload: dict) -> dict:
    resp = httpx.patch(f"{API_BASE}/api/agents/{agent_id}", headers=_headers(), json=payload, timeout=15)
    return _handle(resp)


def delete_agent(agent_id: str) -> dict:
    resp = httpx.delete(f"{API_BASE}/api/agents/{agent_id}", headers=_headers(), timeout=15)
    return _handle(resp)


# --- Telegram ---

def connect_telegram(agent_id: str, bot_token: str) -> dict:
    resp = httpx.post(
        f"{API_BASE}/api/agents/{agent_id}/telegram",
        headers=_headers(),
        json={"bot_token": bot_token},
        timeout=30,
    )
    return _handle(resp)


def disconnect_telegram(agent_id: str) -> dict:
    resp = httpx.delete(f"{API_BASE}/api/agents/{agent_id}/telegram", headers=_headers(), timeout=15)
    return _handle(resp)


# --- API Keys ---

def generate_api_key(agent_id: str) -> dict:
    resp = httpx.post(f"{API_BASE}/api/v1/keys", headers=_headers(), json={"agent_id": agent_id}, timeout=15)
    return _handle(resp)


def list_api_keys() -> list[dict]:
    resp = httpx.get(f"{API_BASE}/api/v1/keys", headers=_headers(), timeout=15)
    data = _handle(resp)
    return data.get("keys", [])


def revoke_api_key(agent_id: str) -> dict:
    resp = httpx.delete(f"{API_BASE}/api/v1/keys/{agent_id}", headers=_headers(), timeout=15)
    return _handle(resp)


# --- Credits ---

def get_platform_stats() -> dict:
    resp = httpx.get(f"{API_BASE}/api/platform/stats", headers=_headers(), timeout=15)
    return _handle(resp)


# --- Chat ---

def chat(api_key: str, message: str, channel: str = "cli") -> dict:
    resp = httpx.post(
        f"{API_BASE}/api/v1/chat",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"message": message, "channel": channel},
        timeout=60,
    )
    return _handle(resp)
