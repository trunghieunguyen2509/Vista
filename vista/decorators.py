from functools import wraps

from flask import redirect, request, session, url_for

from .db import get_db_connection

STAFF_ROLES = ("staff", "admin")


def _session_is_current():
    """False if this session's password predates the account's latest
    password change (or the account no longer exists) — used to log out
    every other device/tab when a customer changes their password."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT session_version FROM users WHERE id = %s", (session.get("user_id"),))
            row = cur.fetchone()
    finally:
        conn.close()
    return bool(row) and row[0] == session.get("session_version")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        if not _session_is_current():
            session.clear()
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        if not _session_is_current():
            session.clear()
            return redirect(url_for("login", next=request.path))
        if session.get("user_role") not in STAFF_ROLES:
            return "Forbidden", 403
        return view(*args, **kwargs)
    return wrapped


def super_admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        if not _session_is_current():
            session.clear()
            return redirect(url_for("login", next=request.path))
        if session.get("user_role") != "admin":
            return "Forbidden", 403
        return view(*args, **kwargs)
    return wrapped
