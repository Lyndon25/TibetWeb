# api/lib/email_service.py
# SMTP email sending — stdlib only, zero dependencies.
# Sends auto-reply to customers and inquiry notifications to the business.

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.qq.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "torchlight@foxmail.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "torchlight@foxmail.com")
NOTIFY_TO = os.environ.get("SMTP_NOTIFY_TO", "torchlight@foxmail.com")

# ── Email templates ────────────────────────────────────────────────────────────

AUTO_REPLY_ZH = """\
<h2>感谢您的咨询！</h2>
<p>您好 {name}，</p>
<p>我们已收到您的西藏旅行需求，将在 <strong>24小时内</strong> 为您定制专属行程方案并回复此邮件。</p>
<p>如有紧急需求，请直接联系我们：</p>
<ul>
  <li>微信：13799412007</li>
  <li>WhatsApp：<a href="https://wa.me/8613799412007">点击聊天</a></li>
</ul>
<p>期待与您一同探索西藏！</p>
<p style="color:#888;">— TibetRide 团队<br>torchlight@foxmail.com</p>
<p style="font-size:0.85rem;color:#999;">
  关注我们：<a href="https://www.facebook.com/profile.php?id=100074488841995">Facebook</a> | <a href="https://youtube.com/@motorcycle2023">YouTube</a>
</p>
"""

AUTO_REPLY_EN = """\
<h2>Thank You for Your Inquiry!</h2>
<p>Hi {name},</p>
<p>We've received your Tibet trip request and will reply with a <strong>personalized itinerary within 24 hours</strong>.</p>
<p>For urgent matters, reach us directly:</p>
<ul>
  <li>WeChat: 13799412007</li>
  <li>WhatsApp: <a href="https://wa.me/8613799412007">Chat now</a></li>
</ul>
<p>Looking forward to exploring Tibet with you!</p>
<p style="color:#888;">— TibetRide Team<br>torchlight@foxmail.com</p>
<p style="font-size:0.85rem;color:#999;">
  Follow us: <a href="https://www.facebook.com/profile.php?id=100074488841995">Facebook</a> | <a href="https://youtube.com/@motorcycle2023">YouTube</a>
</p>
"""

NOTIFY_HTML = """\
<h2>New Inquiry</h2>
<table style="border-collapse:collapse;width:100%%">
  <tr><td style="padding:6px 12px;font-weight:600;color:#666">Name</td><td style="padding:6px">{name}</td></tr>
  <tr style="background:#f9f9f9"><td style="padding:6px 12px;font-weight:600;color:#666">Email</td><td style="padding:6px"><a href="mailto:{email}">{email}</a></td></tr>
  <tr><td style="padding:6px 12px;font-weight:600;color:#666">Travel Date</td><td style="padding:6px">{travel_date}</td></tr>
  <tr style="background:#f9f9f9"><td style="padding:6px 12px;font-weight:600;color:#666">Travelers</td><td style="padding:6px">{travelers}</td></tr>
  <tr><td style="padding:6px 12px;font-weight:600;color:#666">Tour</td><td style="padding:6px">{tour_type}</td></tr>
  <tr style="background:#f9f9f9"><td style="padding:6px 12px;font-weight:600;color:#666">Budget</td><td style="padding:6px">{budget}</td></tr>
  <tr><td style="padding:6px 12px;font-weight:600;color:#666">Message</td><td style="padding:6px">{message}</td></tr>
  <tr style="background:#f9f9f9"><td style="padding:6px 12px;font-weight:600;color:#666">Source</td><td style="padding:6px">{source}</td></tr>
  <tr><td style="padding:6px 12px;font-weight:600;color:#666">Language</td><td style="padding:6px">{lang}</td></tr>
</table>
"""


# ── Public API ─────────────────────────────────────────────────────────────────


def send_email(to: str, subject: str, html_body: str) -> None:
    """Send an HTML email via SMTP."""
    if not SMTP_HOST:
        raise RuntimeError("SMTP_HOST is not configured")

    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if SMTP_PORT == 465:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
    else:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
        server.starttls()

    try:
        if SMTP_USER and SMTP_PASS:
            server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_FROM, to, msg.as_string())
    finally:
        server.quit()


def send_auto_reply(to_email: str, name: str, locale: str = "en") -> None:
    """Send auto-reply confirmation to the customer."""
    if locale.startswith("zh"):
        subject = "收到您的西藏旅行咨询 - TibetRide"
        body = AUTO_REPLY_ZH.format(name=name or "there")
    else:
        subject = "Your Tibet Trip Inquiry Received - TibetRide"
        body = AUTO_REPLY_EN.format(name=name or "there")

    send_email(to_email, subject, body)


def send_new_inquiry_notification(data: dict) -> None:
    """Send notification about a new inquiry to the business owner."""
    body = NOTIFY_HTML.format(
        name=data.get("name", ""),
        email=data.get("email", ""),
        travel_date=data.get("travel_date", ""),
        travelers=data.get("travelers", ""),
        tour_type=data.get("tour_type") or "Not specified",
        budget=data.get("budget") or "Not specified",
        message=(data.get("message") or "—")[:500],
        source=data.get("source", "Website"),
        lang=data.get("lang", "unknown"),
    )
    send_email(NOTIFY_TO, f"New Inquiry from {data.get('name', 'Unknown')}", body)
