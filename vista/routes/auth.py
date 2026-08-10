import secrets
from datetime import timedelta, datetime

from flask import redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .. import app
from ..config import ADMIN_EMAILS, SYDNEY_TZ
from ..db import get_db_connection
from ..email import send_reset_email


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not email or not password:
            error = "Email and password are required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                    if cur.fetchone():
                        error = "An account with that email already exists."
                    else:
                        role = "admin" if email in ADMIN_EMAILS else "customer"
                        cur.execute(
                            "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s) RETURNING id, session_version",
                            (email, generate_password_hash(password), role)
                        )
                        user_id, session_version = cur.fetchone()
                        conn.commit()
                        session["user_id"] = user_id
                        session["user_email"] = email
                        session["user_role"] = role
                        session["session_version"] = session_version
                        return redirect(request.args.get("next") or url_for("cart"))
            finally:
                conn.close()

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    success = "Password updated successfully. Please log in." if request.args.get("reset") == "success" else None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, password_hash, role, session_version FROM users WHERE email = %s", (email,))
                row = cur.fetchone()
        finally:
            conn.close()

        if row and check_password_hash(row[1], password):
            session["user_id"] = row[0]
            session["user_email"] = email
            session["user_role"] = row[2]
            session["session_version"] = row[3]
            return redirect(request.args.get("next") or url_for("cart"))
        error = "Invalid email or password."

    return render_template("login.html", error=error, success=success)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_email", None)
    session.pop("user_role", None)
    session.pop("session_version", None)
    return redirect(url_for("index"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                row = cur.fetchone()
                if row:
                    token = secrets.token_urlsafe(32)
                    expires_at = datetime.now(SYDNEY_TZ) + timedelta(minutes=30)
                    cur.execute(
                        "INSERT INTO password_resets (user_id, token, expires_at) VALUES (%s, %s, %s)",
                        (row[0], token, expires_at)
                    )
                    conn.commit()
                    reset_url = url_for("reset_password", token=token, _external=True)
                    send_reset_email(email, reset_url)
        finally:
            conn.close()

        # Same message whether or not the email exists, so we don't leak which emails are registered
        return render_template("forgot-password.html", sent=True)

    return render_template("forgot-password.html", sent=False)


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, expires_at, used FROM password_resets WHERE token = %s",
                (token,)
            )
            row = cur.fetchone()

            valid = row and not row[2] and row[1] > datetime.now(SYDNEY_TZ)
            if not valid:
                return render_template("reset-password.html", token=token, invalid=True, error=None)

            if request.method == "POST":
                password = request.form.get("password", "")
                confirm_password = request.form.get("confirm_password", "")

                if len(password) < 8:
                    error = "Password must be at least 8 characters."
                elif password != confirm_password:
                    error = "Passwords do not match."
                else:
                    cur.execute(
                        "UPDATE users SET password_hash = %s WHERE id = %s",
                        (generate_password_hash(password), row[0])
                    )
                    cur.execute("UPDATE password_resets SET used = TRUE WHERE token = %s", (token,))
                    conn.commit()
                    return redirect(url_for("login", reset="success"))

                return render_template("reset-password.html", token=token, invalid=False, error=error)
    finally:
        conn.close()

    return render_template("reset-password.html", token=token, invalid=False, error=None)
