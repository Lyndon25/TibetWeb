# api/contact.py
# Vercel Python Serverless Function
# Handles contact form submissions: writes to Notion + sends email via Resend

import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler

# ── Environment Variables (set in Vercel Dashboard) ──────────────────────────
NOTION_TOKEN   = os.environ.get("NOTION_TOKEN")
NOTION_DB_ID   = os.environ.get("NOTION_DB_ID")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
ALERT_EMAIL    = os.environ.get("ALERT_EMAIL", "hello@tibetride.com")
WECHAT_WEBHOOK = os.environ.get("WECHAT_WEBHOOK", "")

# ── Constants ────────────────────────────────────────────────────────────────
NOTION_API_URL = "https://api.notion.com/v1/pages"
RESEND_API_URL = "https://api.resend.com/emails"

# Tour slug → human-readable name mapping (must match customize.html options)
TOUR_NAMES = {
    "lhasa-5-days":        "5 Days Lhasa Essence Tour",
    "lhasa-shigatse-7-days": "7 Days Lhasa to Shigatse",
    "everest-9-days":      "9 Days Everest Base Camp",
    "kailash-12-days":     "12 Days Mount Kailash",
    "custom":              "Fully Custom",
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
        # 1. Read request body
        content_len = int(self.headers.get("Content-Length", 0))
        body_bytes  = self.rfile.read(content_len)
        try:
            data = json.loads(body_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        # 2. Validate required fields
        required = ["name", "email", "travel_date", "travelers"]
        missing  = [f for f in required if not data.get(f)]
        if missing:
            self._send_json(400, {"error": f"Missing fields: {', '.join(missing)}"})
            return

        errors = []

        # 3. Write to Notion
        notion_ok = False
        notion_page_id = None
        if NOTION_TOKEN and NOTION_DB_ID:
            try:
                notion_page_id = _write_to_notion(data)
                notion_ok = True
            except Exception as e:
                errors.append(f"Notion write failed: {e}")
        else:
            errors.append("Notion not configured")

        # 4. Send email via Resend
        email_ok = False
        if RESEND_API_KEY:
            try:
                _send_email(data)
                email_ok = True
            except Exception as e:
                errors.append(f"Email send failed: {e}")
        else:
            errors.append("Resend not configured")

        # 5. Optional: WeChat Work webhook
        if WECHAT_WEBHOOK:
            try:
                _send_wechat(data)
            except Exception as e:
                errors.append(f"WeChat notify failed: {e}")

        # 6. Response
        if notion_ok or email_ok:
            self._send_json(200, {
                "success": True,
                "notion_id": notion_page_id,
                "warnings": errors if errors else None,
            })
        else:
            self._send_json(500, {
                "success": False,
                "error": "All backends failed",
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


# ── Backend implementations ──────────────────────────────────────────────────

def _write_to_notion(data: dict) -> str:
    """Create a new page in the Notion database. Returns the page id."""
    tour_label  = TOUR_NAMES.get(data.get("tour_type", ""), data.get("tour_type", ""))
    budget_label = BUDGET_LABELS.get(data.get("budget", ""), data.get("budget", ""))

    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": {
            "Name": {
                "title": [{"text": {"content": data.get("name", "")}}]
            },
            "Email": {
                "email": data.get("email", "")
            },
            "Travel Date": {
                "date": {"start": data.get("travel_date", "")}
            } if data.get("travel_date") else {"rich_text": [{"text": {"content": ""}}]},
            "Travelers": {
                "number": int(data["travelers"]) if str(data.get("travelers", "")).isdigit() else None
            },
            "Tour": {
                "select": {"name": tour_label or "Not specified"}
            },
            "Budget": {
                "select": {"name": budget_label or "Not specified"}
            },
            "Message": {
                "rich_text": [{"text": {"content": data.get("message", "")}}]
            },
            "Status": {
                "select": {"name": "New"}
            },
            "Source": {
                "select": {"name": data.get("source", "Website")}
            },
        }
    }

    req = urllib.request.Request(
        NOTION_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result.get("id", "")


def _send_email(data: dict):
    """Send notification email via Resend."""
    tour_label   = TOUR_NAMES.get(data.get("tour_type", ""), data.get("tour_type", "Not specified"))
    budget_label = BUDGET_LABELS.get(data.get("budget", ""), data.get("budget", "Not specified"))

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Inter, sans-serif; line-height: 1.6; color: #1c1917;">
  <h2 style="color: #b91c1c;">New TibetTrip Inquiry</h2>
  <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
    <tr><td style="padding: 8px; border-bottom: 1px solid #e5e0d8; font-weight: 600;">Name</td><td style="padding: 8px; border-bottom: 1px solid #e5e0d8;">{data.get('name','')}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #e5e0d8; font-weight: 600;">Email</td><td style="padding: 8px; border-bottom: 1px solid #e5e0d8;">{data.get('email','')}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #e5e0d8; font-weight: 600;">Travel Date</td><td style="padding: 8px; border-bottom: 1px solid #e5e0d8;">{data.get('travel_date','')}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #e5e0d8; font-weight: 600;">Travelers</td><td style="padding: 8px; border-bottom: 1px solid #e5e0d8;">{data.get('travelers','')}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #e5e0d8; font-weight: 600;">Tour</td><td style="padding: 8px; border-bottom: 1px solid #e5e0d8;">{tour_label}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #e5e0d8; font-weight: 600;">Budget</td><td style="padding: 8px; border-bottom: 1px solid #e5e0d8;">{budget_label}</td></tr>
    <tr><td style="padding: 8px; font-weight: 600; vertical-align: top;">Message</td><td style="padding: 8px;">{data.get('message','').replace(chr(10), '<br>')}</td></tr>
  </table>
  <p style="margin-top: 24px; font-size: 0.875rem; color: #78716c;">
    Submitted from TibetRide.com
  </p>
</body>
</html>"""

    payload = {
        "from": "TibetRide <noreply@tibetride.com>",
        "to": [ALERT_EMAIL],
        "subject": f"[TibetRide] New inquiry from {data.get('name', '')}",
        "html": html_body,
        "reply_to": data.get("email", ""),
    }

    req = urllib.request.Request(
        RESEND_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        resp.read()  # consume response


def _send_wechat(data: dict):
    """Send notification via WeChat Work group robot webhook."""
    tour_label = TOUR_NAMES.get(data.get("tour_type", ""), data.get("tour_type", "Not specified"))
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": (
                f"**New TibetRide Inquiry**\n\n"
                f"Name: {data.get('name','')}\n"
                f"Email: {data.get('email','')}\n"
                f"Date: {data.get('travel_date','')}\n"
                f"Travelers: {data.get('travelers','')}\n"
                f"Tour: {tour_label}\n"
                f"Budget: {data.get('budget','Not specified')}\n"
                f"Message: {data.get('message','')[:200]}"
            )
        }
    }
    req = urllib.request.Request(
        WECHAT_WEBHOOK,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()
