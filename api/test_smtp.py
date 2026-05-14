# api/test_smtp.py
# Local test script — verifies SMTP connection and sends a test email.
# Run: python api/test_smtp.py
# Set these env vars first, or edit the values below.

import os
import sys

# Add project root to path for local testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override env for local testing (replace with real values)
os.environ.setdefault("SMTP_HOST", "smtp.qq.com")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USER", "torchlight@foxmail.com")
os.environ.setdefault("SMTP_PASS", "vusliqxkykyibfhc")
os.environ.setdefault("SMTP_FROM", "torchlight@foxmail.com")
os.environ.setdefault("SMTP_NOTIFY_TO", "torchlight@foxmail.com")

from api.lib.email_service import send_email, send_auto_reply, send_new_inquiry_notification

print("SMTP Test Suite")
print("=" * 50)

# Test 1: Simple send
print("\n[1/3] Testing basic SMTP connection...")
try:
    send_email(
        to="torchlight@foxmail.com",
        subject="TibetRide SMTP Test",
        html_body="<h2>SMTP Test</h2><p>If you see this, SMTP is working correctly.</p>",
    )
    print("  OK — test email sent")
except Exception as e:
    print(f"  FAILED: {e}")

# Test 2: Auto-reply (EN)
print("\n[2/3] Testing auto-reply (EN)...")
try:
    send_auto_reply("torchlight@foxmail.com", "Test User", "en")
    print("  OK — English auto-reply sent")
except Exception as e:
    print(f"  FAILED: {e}")

# Test 3: Notification
print("\n[3/3] Testing inquiry notification...")
try:
    send_new_inquiry_notification({
        "name": "Test User",
        "email": "test@example.com",
        "travel_date": "2026-06-15",
        "travelers": "2",
        "tour_type": "lhasa-5-days",
        "budget": "1000-1500",
        "message": "This is a test inquiry from the local test script.",
        "source": "test-script",
        "lang": "en",
    })
    print("  OK — notification email sent")
except Exception as e:
    print(f"  FAILED: {e}")

print("\n" + "=" * 50)
print("Test complete. Check your inbox at torchlight@foxmail.com.")
