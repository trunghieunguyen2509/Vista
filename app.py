from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import requests
import time
import os
import json
import psycopg2
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date, timedelta, datetime, timezone
import secrets



# Initialize flask applkication
app = Flask(__name__)

# 1. Define the currency list data
currencies = [
    {"code": "USD", "name": "United States Dollar", "flag": "us", "margin": 0.02, "denominations": [1, 5, 10, 20, 50, 100]},
    {"code": "GBP", "name": "British Pound Sterling", "flag": "gb", "margin": 0.02, "denominations": [5, 10, 20, 50]},
    {"code": "EUR", "name": "Euro", "flag": "eu", "margin": 0.02, "denominations": [5, 10, 20, 50, 100]},
    {"code": "JPY", "name": "Japanese Yen", "flag": "jp", "margin": 4, "denominations": [1000, 2000, 5000, 10000]},
    {"code": "HKD", "name": "Hong Kong Dollar", "flag": "hk", "margin": 0.2, "denominations": [10, 20, 50, 100, 500, 1000]},
    {"code": "THB", "name": "Thai Baht", "flag": "th", "margin": 1.5, "denominations": [20, 50, 100, 500, 1000]},
    {"code": "SGD", "name": "Singapore Dollar", "flag": "sg", "margin": 0.04, "denominations": [2, 5, 10, 50, 100]},
    {"code": "NZD", "name": "New Zealand Dollar", "flag": "nz", "margin": 0.04, "denominations": [5, 10, 20, 50, 100]},
    {"code": "FJD", "name": "Fijian Dollar", "flag": "fj", "margin": 0.8, "denominations": [5, 10, 20, 50, 100]},
    {"code": "CNY", "name": "Chinese Yuan", "flag": "cn", "margin": 0.2, "denominations": [1, 5, 10, 20, 50, 100]},
    {"code": "CAD", "name": "Canadian Dollar", "flag": "ca", "margin": 0.04, "denominations": [5, 10, 20, 50, 100]},
    {"code": "IDR", "name": "Indonesian Rupiah", "flag": "id", "margin": 900, "denominations": [1000, 2000, 5000, 10000, 20000, 50000, 100000]},
    {"code": "PHP", "name": "Philippine Peso", "flag": "ph", "margin": 3.5, "denominations": [20, 50, 100, 200, 500, 1000]},
    {"code": "INR", "name": "Indian Rupee", "flag": "in", "margin": 5.5, "denominations": [10, 20, 50, 100, 200, 500]},
    {"code": "AED", "name": "United Arab Emirates Dirham", "flag": "ae", "margin": 0.2, "denominations": [5, 10, 20, 50, 100, 200, 500]},
    {"code": "KRW", "name": "South Korean Won", "flag": "kr", "margin": 90, "denominations": [1000, 5000, 10000, 50000]},
    {"code": "MYR", "name": "Malaysian Ringgit", "flag": "my", "margin": 0.2, "denominations": [1, 5, 10, 20, 50, 100]},
    {"code": "ZAR", "name": "South African Rand", "flag": "za", "margin": 0, "denominations": [10, 20, 50, 100, 200]},
    {"code": "VND", "name": "Vietnamese Dong", "flag": "vn", "margin": 1500, "denominations": [10000, 20000, 50000, 100000, 200000, 500000]},
    {"code": "TWD", "name": "New Taiwan Dollar", "flag": "tw", "margin": 2, "denominations": [100, 200, 500, 1000]},
    {"code": "CHF", "name": "Swiss Franc", "flag": "ch", "margin": 0.022, "denominations": [10, 20, 50, 100, 200]},
    {"code": "TRY", "name": "Turkish Lira", "flag": "tr", "margin": 3.5, "denominations": [5, 10, 20, 50, 100, 200]},
    {"code": "XPF", "name": "CFP Franc", "flag": "pf", "margin": 0, "denominations": [500, 1000, 5000, 10000]},
    {"code": "DKK", "name": "Danish Krone", "flag": "dk", "margin": 0, "denominations": [50, 100, 200, 500, 1000]},
    {"code": "SEK", "name": "Swedish Krona", "flag": "se", "margin": 0, "denominations": [20, 50, 100, 200, 500]},
    {"code": "CZK", "name": "Czech Koruna", "flag": "cz", "margin": 0, "denominations": [100, 200, 500, 1000, 2000]},
    {"code": "PLN", "name": "Polish Zloty", "flag": "pl", "margin": 0, "denominations": [10, 20, 50, 100, 200]},
    {"code": "HUF", "name": "Hungarian Forint", "flag": "hu", "margin": 0, "denominations": [500, 1000, 2000, 5000, 10000]},
    {"code": "MXN", "name": "Mexican Peso", "flag": "mx", "margin": 0, "denominations": [20, 50, 100, 200, 500]},
    {"code": "VUV", "name": "Vanuatu Vatu", "flag": "vu", "margin": 0, "denominations": [500, 1000, 2000, 5000, 10000]},
    {"code": "NOK", "name": "Norwegian Krone", "flag": "no", "margin": 0, "denominations": [50, 100, 200, 500, 1000]},
    {"code": "AUD", "name": "Australian Dollar", "flag": "au", "margin": 0, "denominations": [0.01, 1, 100]}
]


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    items JSONB NOT NULL,
                    total_aud NUMERIC(12, 2) NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reservations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    items JSONB NOT NULL,
                    total_aud NUMERIC(12, 2) NOT NULL,
                    pickup_date DATE NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    used BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """)


        conn.commit()
    finally:
        conn.close()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        if session.get("user_email") not in admin_emails:
            return "Forbidden", 403
        return view(*args, **kwargs)
    return wrapped


#Handle API
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
api_key = os.getenv("EXCHANGE_API_KEY")
resend_api_key = os.getenv("RESEND_API_KEY")
resend_from_email = os.getenv("RESEND_FROM_EMAIL")
admin_emails = {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}
url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/AUD"

# Extract the conversion rates
def fetch_exchange_rate():
    try:
        # Get data from API
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # 2. Parse JSON body
        data = response.json()
        all_rates = data["conversion_rates"]
        
        # 3. Update currencies list
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        for currency in currencies:
            code = currency["code"]
            raw_rate = all_rates.get(code)
            # Fallback to None if code isn't found
            currency["rate"] = raw_rate - currency["margin"] if raw_rate is not None else None
            print(f"[{current_time}] Updated {code}: {currency['rate']}")

    except requests.exceptions.RequestException as e:
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{current_time}] API Request failed: {e}")

def send_reset_email(to_email, reset_url):
    try:
        requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {resend_api_key}"},
            json={
                "from": resend_from_email,
                "to": to_email,
                "subject": "Reset your Vista password",
                "html": f'<p>Click the link below to reset your password. This link expires in 30 minutes.</p><p><a href="{reset_url}">{reset_url}</a></p>'
            },
            timeout=10
        )
    except requests.exceptions.RequestException as e:
        print(f"Resend email failed: {e}")

# Define route
@app.route("/")
def index():
    return render_template('index.html', currencies=currencies)

@app.route("/buy-currency")
def buy_currency():
    return render_template('buy-currency.html', currencies=currencies)

def find_currency(code):
    return next((c for c in currencies if c["code"] == code), None)

@app.context_processor
def inject_cart_count():
    is_admin = session.get("user_email") in admin_emails
    return {"cart_count": len(session.get("cart", [])), "is_admin": is_admin}


def get_cart_view():
    raw_items = session.get("cart", [])
    cart_items = []
    total_aud = 0
    for i, item in enumerate(raw_items):
        currency = find_currency(item["code"])
        if not currency or not currency.get("rate"):
            continue
        aud_cost = item["amount"] / currency["rate"]
        total_aud += aud_cost
        cart_items.append({
            "index": i,
            "code": currency["code"],
            "name": currency["name"],
            "flag": currency["flag"],
            "amount": item["amount"],
            "rate": currency["rate"],
            "aud_cost": aud_cost
        })
    return cart_items, total_aud

def get_reserve_view():
    raw_items = session.get("reserve_cart", [])
    reserve_items = []
    total_aud = 0
    for i, item in enumerate(raw_items):
        currency = find_currency(item["code"])
        if not currency or not currency.get("rate"):
            continue
        aud_cost = item["amount"] / currency["rate"]
        total_aud += aud_cost
        reserve_items.append({
            "index": i,
            "code": currency["code"],
            "name": currency["name"],
            "flag": currency["flag"],
            "amount": item["amount"],
            "rate": currency["rate"],
            "aud_cost": aud_cost
        })
    return reserve_items, total_aud

@app.route("/cart")
def cart():
    cart_items, total_aud = get_cart_view()
    return render_template("cart.html", currencies=currencies, cart_items=cart_items, total_aud=total_aud)

@app.route("/cart/add", methods=["POST"])
def cart_add():
    code = request.form.get("code")
    try:
        amount = float(request.form.get("amount", ""))
    except ValueError:
        amount = None

    if find_currency(code) and amount and amount > 0:
        cart_items = session.get("cart", [])
        cart_items.append({"code": code, "amount": amount})
        session["cart"] = cart_items

    return redirect(url_for("cart"))

@app.route("/cart/remove/<int:index>", methods=["POST"])
def cart_remove(index):
    cart_items = session.get("cart", [])
    if 0 <= index < len(cart_items):
        cart_items.pop(index)
        session["cart"] = cart_items
    return redirect(url_for("cart"))

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
                        cur.execute(
                            "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                            (email, generate_password_hash(password))
                        )
                        user_id = cur.fetchone()[0]
                        conn.commit()
                        session["user_id"] = user_id
                        session["user_email"] = email
                        return redirect(request.args.get("next") or url_for("cart"))
            finally:
                conn.close()

    return render_template("register.html", error=error)

@app.route("/login", methods=["GET", "POST"])
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
                cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
                row = cur.fetchone()
        finally:
            conn.close()

        if row and check_password_hash(row[1], password):
            session["user_id"] = row[0]
            session["user_email"] = email
            return redirect(request.args.get("next") or url_for("cart"))
        error = "Invalid email or password."

    return render_template("login.html", error=error, success=success)

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_email", None)
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
                    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
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

            valid = row and not row[2] and row[1] > datetime.now(timezone.utc)

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

@app.route("/cart/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_items, total_aud = get_cart_view()
    if not cart_items:
        return redirect(url_for("cart"))

    if request.method == "POST":
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO orders (user_id, items, total_aud) VALUES (%s, %s, %s) RETURNING id",
                    (session["user_id"], json.dumps(cart_items), total_aud)
                )
                order_id = cur.fetchone()[0]
            conn.commit()
        finally:
            conn.close()

        session["cart"] = []
        return render_template("checkout-success.html", order_id=order_id, cart_items=cart_items, total_aud=total_aud)

    return render_template("checkout.html", cart_items=cart_items, total_aud=total_aud)

@app.route("/reserve")
def reserve():
    reserve_items, total_aud = get_reserve_view()
    return render_template("reserve.html", currencies=currencies, reserve_items=reserve_items, total_aud=total_aud)

@app.route("/reserve/add", methods=["POST"])
def reserve_add():
    code = request.form.get("code")
    try:
        amount = float(request.form.get("amount", ""))
    except ValueError:
        amount = None

    if find_currency(code) and amount and amount > 0:
        reserve_items = session.get("reserve_cart", [])
        reserve_items.append({"code": code, "amount": amount})
        session["reserve_cart"] = reserve_items

    return redirect(url_for("reserve"))

@app.route("/reserve/remove/<int:index>", methods=["POST"])
def reserve_remove(index):
    reserve_items = session.get("reserve_cart", [])
    if 0 <= index < len(reserve_items):
        reserve_items.pop(index)
        session["reserve_cart"] = reserve_items
    return redirect(url_for("reserve"))

@app.route("/reserve/checkout", methods=["GET", "POST"])
@login_required
def reserve_checkout():
    reserve_items, total_aud = get_reserve_view()
    if not reserve_items:
        return redirect(url_for("reserve"))

    min_pickup_date = (date.today() + timedelta(days=1)).isoformat()

    if request.method == "POST":
        try:
            pickup_date = date.fromisoformat(request.form.get("pickup_date", ""))
        except ValueError:
            pickup_date = None

        if not pickup_date or pickup_date < date.today() + timedelta(days=1):
            return render_template("reserve-checkout.html", reserve_items=reserve_items,
                                    total_aud=total_aud, min_pickup_date=min_pickup_date,
                                    error="Please choose a valid pick-up date (at least 1 day from today).")

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO reservations (user_id, items, total_aud, pickup_date) VALUES (%s, %s, %s, %s) RETURNING id",
                    (session["user_id"], json.dumps(reserve_items), total_aud, pickup_date)
                )
                reservation_id = cur.fetchone()[0]
            conn.commit()
        finally:
            conn.close()

        session["reserve_cart"] = []
        return render_template("reserve-success.html", reservation_id=reservation_id,
                                reserve_items=reserve_items, total_aud=total_aud, pickup_date=pickup_date)

    return render_template("reserve-checkout.html", reserve_items=reserve_items,
                            total_aud=total_aud, min_pickup_date=min_pickup_date, error=None)

@app.route("/admin/reservations")
@admin_required
def admin_reservations():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.id, u.email, r.items, r.total_aud, r.pickup_date, r.status, r.created_at
                FROM reservations r
                JOIN users u ON u.id = r.user_id
                ORDER BY r.pickup_date ASC, r.created_at ASC
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    reservations = [{
        "id": row[0], "email": row[1], "items": row[2], "total_aud": row[3],
        "pickup_date": row[4], "status": row[5], "created_at": row[6]
    } for row in rows]
    return render_template("admin-reservations.html", reservations=reservations)

@app.route("/admin/reservations/<int:reservation_id>/status", methods=["POST"])
@admin_required
def admin_reservation_status(reservation_id):
    status = request.form.get("status")
    if status in ("pending", "fulfilled", "cancelled"):
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE reservations SET status = %s WHERE id = %s", (status, reservation_id))
            conn.commit()
        finally:
            conn.close()
    return redirect(url_for("admin_reservations"))

@app.route("/admin/orders")
@admin_required
def admin_orders():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.id, u.email, o.items, o.total_aud, o.created_at
                FROM orders o
                JOIN users u ON u.id = o.user_id
                ORDER BY o.created_at DESC
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    orders = [{
        "id": row[0], "email": row[1], "items": row[2], "total_aud": row[3], "created_at": row[4]
    } for row in rows]
    return render_template("admin-orders.html", orders=orders)

DEBUG = True
init_db()
fetch_exchange_rate()
if not DEBUG or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_exchange_rate, 'interval', hours=1)
    scheduler.start()

if __name__ == '__main__':
    app.run(debug=DEBUG)
    


