# api/contact.py
# Vercel Python Serverless Function
# Stores inquiries to Supabase + Feishu Bitable, sends email replies + bot notifications

import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler

from api.lib.supabase_client import create_inquiry
from api.lib.email_service import send_auto_reply, send_new_inquiry_notification

# ── Environment Variables ────────────────────────────────────────────────────
FEISHU_APP_ID     = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_APP_TOKEN  = os.environ.get("FEISHU_APP_TOKEN", "")
FEISHU_TABLE_ID   = os.environ.get("FEISHU_TABLE_ID", "")
FEISHU_WEBHOOK    = os.environ.get("FEISHU_WEBHOOK", "")

# ── Constants ────────────────────────────────────────────────────────────────
FEISHU_AUTH_URL  = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
FEISHU_BASE_URL  = "https://open.feishu.cn/open-apis/bitable/v1/apps"

TOUR_NAMES = {
    "lhasa-5-days":          "5 Days Lhasa Essence Tour",
    "lhasa-shigatse-7-days": "7 Days Lhasa to Shigatse",
    "everest-9-days":        "9 Days Everest Base Camp",
    "kailash-12-days":       "12 Days Mount Kailash",
    "custom":                "Fully Custom",
}

BUDGET_LABELS = {
    "under-1000": "Under USD 1,000 / person",
    "1000-1500":  "USD 1,000 - 1,500 / person",
    "1500-2500":  "USD 1,500 - 2,500 / person",
    "2500+":      "USD 2,500+ / person",
}


class handler(BaseHTTPRequestHandler):
    """Vercel Serverless Handler."""

    def do_OPTIONS(self):
        self._send_cors(200)
        self.end_headers()

    def do_POST(self):
        # 1. Read body
        content_len = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_len)
        try:
            data = json.loads(body_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        # 2. Validate
        required = ["name", "email", "travel_date", "travelers"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            self._send_json(400, {"error": f"Missing fields: {', '.join(missing)}"})
            return

        errors = []
        notifications = []

        # 3. Write to Supabase (primary data store)
        try:
            supabase_id = create_inquiry(data)
        except Exception as e:
            errors.append(f"Supabase: {e}")

        # 4. Send auto-reply email to customer
        try:
            send_auto_reply(
                to_email=data["email"],
                name=data.get("name", ""),
                locale=data.get("lang", "en"),
            )
            notifications.append("auto-reply sent")
        except Exception as e:
            errors.append(f"Auto-reply email: {e}")

        # 5. Send notification email to business
        try:
            send_new_inquiry_notification(data)
            notifications.append("owner notified")
        except Exception as e:
            errors.append(f"Notify email: {e}")

        # 6. Write to Feishu Bitable (admin view, redundancy)
        if FEISHU_APP_ID and FEISHU_APP_SECRET and FEISHU_APP_TOKEN and FEISHU_TABLE_ID:
            try:
                token = _get_tenant_token()
                _create_bitable_record(token, data)
            except Exception as e:
                errors.append(f"Feishu bitable: {e}")

        # 7. Send Feishu group bot notification
        if FEISHU_WEBHOOK:
            try:
                _send_feishu_bot(data)
            except Exception as e:
                errors.append(f"Feishu bot: {e}")

        # 8. Response — email is the critical path
        if notifications:
            self._send_json(200, {
                "success": True,
                "notifications": notifications,
                "warnings": errors if errors else None,
            })
        else:
            self._send_json(500, {
                "success": False,
                "error": "Failed to send email notifications",
                "details": errors,
            })

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _send_cors(self, code):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json")

    def _send_json(self, code, payload):
        self._send_cors(code)
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))


def _get_tenant_token() -> str:
    """Get Feishu tenant_access_token via app_id + app_secret."""
    payload = json.dumps({
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET,
    }).encode("utf-8")
    req = urllib.request.Request(
        FEISHU_AUTH_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        if result.get("code") != 0:
            raise RuntimeError(f"Feishu auth error: {result}")
        return result["tenant_access_token"]


def _create_bitable_record(token: str, data: dict) -> str:
    """Create a new record in Feishu Bitable. Returns record_id."""
    tour_label = TOUR_NAMES.get(
        data.get("tour_type", ""), data.get("tour_type", "") or "Not specified"
    )
    budget_label = BUDGET_LABELS.get(
        data.get("budget", ""), data.get("budget", "") or "Not specified"
    )

    url = f"{FEISHU_BASE_URL}/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"
    payload = {
        "fields": {
            "姓名": data.get("name", ""),
            "邮箱": data.get("email", ""),
            "出发日期": data.get("travel_date", ""),
            "人数": int(data["travelers"]) if str(data.get("travelers", "")).isdigit() else 0,
            "线路": tour_label,
            "预算": budget_label,
            "留言": data.get("message", ""),
            "状态": "新咨询",
            "来源": data.get("source", "Website"),
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        if result.get("code") != 0:
            raise RuntimeError(f"Bitable create error: {result}")
        return result["data"]["record"]["record_id"]


def _send_feishu_bot(data: dict):
    """Send interactive card to Feishu group via webhook."""
    tour_label = TOUR_NAMES.get(
        data.get("tour_type", ""), data.get("tour_type", "Not specified")
    )
    budget_label = BUDGET_LABELS.get(
        data.get("budget", ""), data.get("budget", "Not specified")
    )

    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "🎒 新旅行咨询"},
                "template": "red",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"**姓名：**{data.get('name', '')}\n"
                            f"**邮箱：**{data.get('email', '')}\n"
                            f"**出发日期：**{data.get('travel_date', '')}\n"
                            f"**人数：**{data.get('travelers', '')}\n"
                            f"**线路：**{tour_label}\n"
                            f"**预算：**{budget_label}\n"
                            f"**留言：**{data.get('message', '')[:300]}"
                        ),
                    },
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📧 发送邮件回复"},
                            "type": "primary",
                            "url": f"mailto:{data.get('email', '')}",
                        }
                    ],
                },
            ],
        },
    }

    req = urllib.request.Request(
        FEISHU_WEBHOOK,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        if result.get("code") != 0:
            raise RuntimeError(f"Feishu bot error: {result}")
