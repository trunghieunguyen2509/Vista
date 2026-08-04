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


#Handle API
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
api_key = os.getenv("EXCHANGE_API_KEY")
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

# Define route
@app.route("/")
def index():
    return render_template('index.html', currencies=currencies)

@app.route("/buy-currency")
def buy_currency():
    return render_template('buy-currency.html', currencies=currencies)

def find_currency(code):
    return next((c for c in currencies if c["code"] == code), None)

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
def login():
    error = None
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

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_email", None)
    return redirect(url_for("index"))

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

DEBUG = True
init_db()
fetch_exchange_rate()
if not DEBUG or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_exchange_rate, 'interval', hours=1)
    scheduler.start()

if __name__ == '__main__':
    app.run(debug=DEBUG)
    


