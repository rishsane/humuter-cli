"""HTTP client for the Humuter API."""

import httpx
from humuter.config import get_token, get_refresh_token, save_credentials, load_credentials, API_BASE


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


def _try_refresh() -> bool:
    """Attempt to refresh the access token. Returns True if successful."""
    refresh_token = get_refresh_token()
    if not refresh_token:
        return False
    try:
        resp = httpx.post(
            f"{API_BASE}/api/auth/cli/refresh",
            json={"refresh_token": refresh_token},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            creds = load_credentials() or {}
            save_credentials(
                data["token"],
                data.get("user_id", creds.get("user_id", "")),
                data.get("refresh_token", refresh_token),
            )
            return True
    except Exception:
        pass
    return False


def _handle(resp: httpx.Response) -> dict:
    if resp.status_code == 401:
        raise ApiError(401, "Unauthorized. Run `humuter login` first.")
    data = resp.json()
    if resp.status_code >= 400:
        raise ApiError(resp.status_code, data.get("error", "Unknown error"))
    return data


def _request(method: str, url: str, **kwargs) -> dict:
    """Make an API request with automatic token refresh on 401."""
    kwargs.setdefault("headers", _headers())
    kwargs.setdefault("timeout", 15)
    resp = getattr(httpx, method)(url, **kwargs)
    if resp.status_code == 401 and _try_refresh():
        kwargs["headers"] = _headers()
        resp = getattr(httpx, method)(url, **kwargs)
    return _handle(resp)


# --- Auth (no auto-refresh for auth endpoints) ---

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
    data = _request("get", f"{API_BASE}/api/agents")
    return data.get("agents", [])


def get_agent(agent_id: str) -> dict:
    data = _request("get", f"{API_BASE}/api/agents/{agent_id}")
    return data.get("agent", data)


def create_agent(payload: dict) -> dict:
    return _request("post", f"{API_BASE}/api/agents", json=payload, timeout=30)


def update_agent(agent_id: str, payload: dict) -> dict:
    return _request("patch", f"{API_BASE}/api/agents/{agent_id}", json=payload)


def delete_agent(agent_id: str) -> dict:
    return _request("delete", f"{API_BASE}/api/agents/{agent_id}")


# --- Telegram ---

def connect_telegram(agent_id: str, bot_token: str) -> dict:
    return _request(
        "post",
        f"{API_BASE}/api/agents/{agent_id}/telegram",
        json={"bot_token": bot_token},
        timeout=30,
    )


def disconnect_telegram(agent_id: str) -> dict:
    return _request("delete", f"{API_BASE}/api/agents/{agent_id}/telegram")


# --- API Keys ---

def generate_api_key(agent_id: str) -> dict:
    return _request("post", f"{API_BASE}/api/v1/keys", json={"agent_id": agent_id})


def list_api_keys() -> list[dict]:
    data = _request("get", f"{API_BASE}/api/v1/keys")
    return data.get("keys", [])


def revoke_api_key(agent_id: str) -> dict:
    return _request("delete", f"{API_BASE}/api/v1/keys/{agent_id}")


# --- Credits ---

def get_platform_stats() -> dict:
    return _request("get", f"{API_BASE}/api/platform/stats")


# --- Chat ---

def chat(api_key: str, message: str, channel: str = "cli") -> dict:
    resp = httpx.post(
        f"{API_BASE}/api/v1/chat",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"message": message, "channel": channel},
        timeout=60,
    )
    return _handle(resp)
