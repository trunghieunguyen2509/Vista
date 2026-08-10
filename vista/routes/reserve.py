import json
from datetime import date, datetime, timedelta

from flask import redirect, render_template, request, session, url_for

from .. import app
from ..config import SYDNEY_TZ
from ..currencies import currencies
from ..db import get_db_connection
from ..decorators import login_required
from ..shopping import add_session_item, get_session_list_view, remove_session_item

RESERVE_KEY = "reserve_cart"
MIN_PICKUP_LEAD_DAYS = 4
NOTES_MAX_LENGTH = 500


@app.route("/reserve")
def reserve():
    reserve_items, total_aud = get_session_list_view(RESERVE_KEY)
    return render_template("reserve.html", currencies=currencies, reserve_items=reserve_items, total_aud=total_aud)


@app.route("/reserve/add", methods=["POST"])
def reserve_add():
    code = request.form.get("code")
    try:
        amount = float(request.form.get("amount", ""))
    except ValueError:
        amount = None

    add_session_item(RESERVE_KEY, code, amount)
    return redirect(url_for("reserve"))


@app.route("/reserve/remove/<int:index>", methods=["POST"])
def reserve_remove(index):
    remove_session_item(RESERVE_KEY, index)
    return redirect(url_for("reserve"))


@app.route("/reserve/checkout", methods=["GET", "POST"])
@login_required
def reserve_checkout():
    reserve_items, total_aud = get_session_list_view(RESERVE_KEY)
    if not reserve_items:
        return redirect(url_for("reserve"))

    min_pickup_date = (datetime.now(SYDNEY_TZ).date() + timedelta(days=MIN_PICKUP_LEAD_DAYS)).isoformat()

    if request.method == "POST":
        try:
            pickup_date = date.fromisoformat(request.form.get("pickup_date", ""))
        except ValueError:
            pickup_date = None

        notes = request.form.get("notes", "").strip()[:NOTES_MAX_LENGTH] or None

        if not pickup_date or pickup_date < datetime.now(SYDNEY_TZ).date() + timedelta(days=MIN_PICKUP_LEAD_DAYS):
            return render_template("reserve-checkout.html", reserve_items=reserve_items,
                                    total_aud=total_aud, min_pickup_date=min_pickup_date,
                                    notes=notes,
                                    error=f"Please choose a valid pick-up date (at least {MIN_PICKUP_LEAD_DAYS} days from today).")

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO reservations (user_id, items, total_aud, pickup_date, notes) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (session["user_id"], json.dumps(reserve_items), total_aud, pickup_date, notes)
                )
                reservation_id = cur.fetchone()[0]
            conn.commit()
        finally:
            conn.close()

        session[RESERVE_KEY] = []
        return render_template("reserve-success.html", reservation_id=reservation_id,
                                reserve_items=reserve_items, total_aud=total_aud, pickup_date=pickup_date,
                                notes=notes)

    return render_template("reserve-checkout.html", reserve_items=reserve_items,
                            total_aud=total_aud, min_pickup_date=min_pickup_date, notes=None, error=None)
