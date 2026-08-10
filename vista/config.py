import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

SYDNEY_TZ = ZoneInfo("Australia/Sydney")

DEBUG = True

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL")
ADMIN_EMAILS = {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}
