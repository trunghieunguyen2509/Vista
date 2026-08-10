import json

from flask import redirect, render_template, request, session, url_for

from .. import app
from ..currencies import currencies
from ..db import get_db_connection
from ..decorators import login_required
from ..shopping import add_session_item, get_session_list_view, remove_session_item

CART_KEY = "cart"


@app.route("/cart")
def cart():
    cart_items, total_aud = get_session_list_view(CART_KEY)
    return render_template("cart.html", currencies=currencies, cart_items=cart_items, total_aud=total_aud)


@app.route("/cart/add", methods=["POST"])
def cart_add():
    code = request.form.get("code")
    try:
        amount = float(request.form.get("amount", ""))
    except ValueError:
        amount = None

    add_session_item(CART_KEY, code, amount)
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:index>", methods=["POST"])
def cart_remove(index):
    remove_session_item(CART_KEY, index)
    return redirect(url_for("cart"))


@app.route("/cart/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    cart_items, total_aud = get_session_list_view(CART_KEY)
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

        session[CART_KEY] = []
        return render_template("checkout-success.html", order_id=order_id, cart_items=cart_items, total_aud=total_aud)

    return render_template("checkout.html", cart_items=cart_items, total_aud=total_aud)
