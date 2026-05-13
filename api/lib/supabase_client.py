# api/lib/supabase_client.py
# Supabase REST API client — stdlib only, zero dependencies.
# Interacts with Supabase PostgreSQL via PostgREST auto-generated API.

import os
import json
import urllib.request
import urllib.error

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")  # service_role key

TABLE = "inquiries"
BASE_PATH = f"/rest/v1/{TABLE}"


def _request(method: str, path: str, body: dict | None = None, params: str | None = None) -> dict:
    """Send a request to Supabase PostgREST API."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

    url = f"{SUPABASE_URL.rstrip('/')}{path}"
    if params:
        url += f"?{params}"

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    if method == "POST":
        headers["Prefer"] = "return=representation"

    data_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8") if e.fp else str(e)
        raise RuntimeError(f"Supabase {method} {path} failed ({e.code}): {detail}") from e


def create_inquiry(data: dict) -> int:
    """Insert a new inquiry. Returns the auto-generated id."""
    record = {
        "name": data.get("name", ""),
        "email": data.get("email", ""),
        "travel_date": data.get("travel_date", ""),
        "travelers": int(data["travelers"]) if str(data.get("travelers", "")).isdigit() else 0,
        "tour_type": data.get("tour_type") or None,
        "budget": data.get("budget") or None,
        "message": data.get("message") or None,
        "source": data.get("source", "Website"),
        "status": "new",
        "lang": data.get("lang", "unknown"),
    }
    result = _request("POST", BASE_PATH, body=record)
    rows = result if isinstance(result, list) else [result]
    return rows[0]["id"]


def check_duplicate(email: str, within_hours: int = 1) -> bool:
    """Check if the same email submitted within the last N hours."""
    params = f"email=eq.{urllib.request.quote(email)}&order=created_at.desc&limit=1"
    rows = _request("GET", BASE_PATH, params=params)
    if not rows:
        return False
    from datetime import datetime, timezone, timedelta
    created_at = rows[0].get("created_at", "")
    if not created_at:
        return False
    try:
        ts = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - ts < timedelta(hours=within_hours)
    except (ValueError, TypeError):
        return False
