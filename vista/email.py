import requests

from .config import RESEND_API_KEY, RESEND_FROM_EMAIL


def send_reset_email(to_email, reset_url):
    try:
        requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": "Reset your Vista password",
                "html": f'<p>Click the link below to reset your password. This link expires in 30 minutes.</p><p><a href="{reset_url}">{reset_url}</a></p>'
            },
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        print(f"Resend email failed: {e}")


def send_password_changed_email(to_email):
    try:
        requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": RESEND_FROM_EMAIL,
                "to": to_email,
                "subject": "Your Vista password was changed",
                "html": "<p>Your password was just changed. You've been logged out of any other active sessions.</p>"
                        "<p>If this wasn't you, reset your password immediately and contact support.</p>"
            },
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        print(f"Resend email failed: {e}")
