# api/contact.py
# Vercel Python Serverless Function
# Handles contact form submissions: sends notification to Feishu group via webhook

import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler

# ── Environment Variables (set in Vercel Dashboard) ──────────────────────────
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")

# ── Tour / Budget mapping ────────────────────────────────────────────────────
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
        # 1. Read request body
        content_len = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_len)
        try:
            data = json.loads(body_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        # 2. Validate required fields
        required = ["name", "email", "travel_date", "travelers"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            self._send_json(400, {"error": f"Missing fields: {', '.join(missing)}"})
            return

        # 3. Check webhook config
        if not FEISHU_WEBHOOK:
            self._send_json(500, {"error": "Feishu webhook not configured"})
            return

        # 4. Send to Feishu
        try:
            _send_feishu(data)
            self._send_json(200, {"success": True})
        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

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


def _send_feishu(data: dict):
    """Send an interactive card message to Feishu group via webhook."""
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
                "title": {
                    "tag": "plain_text",
                    "content": "🎒 新旅行咨询"
                },
                "template": "red"
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
                        )
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "📧 发送邮件回复"
                            },
                            "type": "primary",
                            "url": f"mailto:{data.get('email', '')}"
                        }
                    ]
                }
            ]
        }
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
            raise RuntimeError(f"Feishu API error: {result}")
