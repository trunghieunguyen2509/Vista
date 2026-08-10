from flask import render_template, request, session

from .. import app
from ..currencies import currencies
from ..db import get_db_connection
from ..decorators import STAFF_ROLES


@app.route("/")
def index():
    return render_template('index.html', currencies=currencies)


@app.route("/buy-currency")
def buy_currency():
    return render_template('buy-currency.html', currencies=currencies)


@app.context_processor
def inject_cart_count():
    is_admin = session.get("user_role") in STAFF_ROLES
    is_super_admin = session.get("user_role") == "admin"
    pending_reservations = 0
    pending_orders = 0
    if is_admin:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM reservations WHERE status = 'pending'")
                pending_reservations = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
                pending_orders = cur.fetchone()[0]
        finally:
            conn.close()
    return {
        "cart_count": len(session.get("cart", [])),
        "is_admin": is_admin,
        "is_super_admin": is_super_admin,
        "pending_reservations": pending_reservations,
        "pending_orders": pending_orders,
        "in_account_area": request.path.startswith("/account"),
    }
