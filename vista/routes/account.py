from datetime import date, timedelta

from flask import redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .. import app
from ..activity import get_activity
from ..config import SYDNEY_TZ
from ..db import get_db_connection
from ..decorators import login_required
from ..email import send_password_changed_email
from ..pagination import paginate_query

ACTIVE_STATUSES = ("pending",)
HISTORY_STATUSES = ("fulfilled", "cancelled")


def _current_page():
    try:
        return int(request.args.get("page", 1))
    except ValueError:
        return 1


def _parse_date(value):
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


@app.route("/account")
@login_required
def account_overview():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT email, full_name, created_at FROM users WHERE id = %s", (session["user_id"],))
            email, full_name, member_since = cur.fetchone()

            cur.execute("SELECT COUNT(*) FROM orders WHERE user_id = %s AND status = 'pending'", (session["user_id"],))
            active_orders = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM reservations WHERE user_id = %s AND status = 'pending'", (session["user_id"],))
            active_reservations = cur.fetchone()[0]

            cur.execute("""
                SELECT id, total_aud, status, created_at FROM orders
                WHERE user_id = %s ORDER BY created_at DESC LIMIT 3
            """, (session["user_id"],))
            recent_orders = cur.fetchall()

            cur.execute("""
                SELECT id, total_aud, status, pickup_date, created_at FROM reservations
                WHERE user_id = %s ORDER BY created_at DESC LIMIT 3
            """, (session["user_id"],))
            recent_reservations = cur.fetchall()
    finally:
        conn.close()

    return render_template(
        "account-overview.html", active_section="overview", breadcrumbs=[("Overview", None)],
        full_name=full_name, email=email, member_since=member_since.astimezone(SYDNEY_TZ),
        active_orders=active_orders, active_reservations=active_reservations,
        recent_orders=[{"id": r[0], "total_aud": r[1], "status": r[2], "created_at": r[3].astimezone(SYDNEY_TZ)} for r in recent_orders],
        recent_reservations=[{"id": r[0], "total_aud": r[1], "status": r[2], "pickup_date": r[3], "created_at": r[4].astimezone(SYDNEY_TZ)} for r in recent_reservations],
    )


@app.route("/account/profile", methods=["GET", "POST"])
@login_required
def account_profile():
    error = None
    success = None

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()[:120]
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()[:40]
        address = request.form.get("address", "").strip()[:300]

        if not email:
            error = "Email is required."
        else:
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, session["user_id"]))
                    if cur.fetchone():
                        error = "That email is already in use by another account."
                    else:
                        cur.execute(
                            "UPDATE users SET full_name = %s, email = %s, phone = %s, address = %s WHERE id = %s",
                            (full_name or None, email, phone or None, address or None, session["user_id"])
                        )
                        conn.commit()
                        session["user_email"] = email
                        success = "Profile updated successfully."
            finally:
                conn.close()

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT full_name, email, phone, address FROM users WHERE id = %s", (session["user_id"],))
            full_name, email, phone, address = cur.fetchone()
    finally:
        conn.close()

    return render_template(
        "account-profile.html", active_section="profile", breadcrumbs=[("Profile", None)],
        error=error, success=success,
        full_name=full_name or "", email=email, phone=phone or "", address=address or "",
    )


@app.route("/account/security", methods=["GET", "POST"])
@login_required
def account_security():
    error = None
    success = None

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT password_hash FROM users WHERE id = %s", (session["user_id"],))
                current_hash = cur.fetchone()[0]

            if not check_password_hash(current_hash, current_password):
                error = "Current password is incorrect."
            elif len(new_password) < 8:
                error = "New password must be at least 8 characters."
            elif new_password != confirm_password:
                error = "New passwords do not match."
            else:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE users SET password_hash = %s, session_version = session_version + 1 "
                        "WHERE id = %s RETURNING session_version",
                        (generate_password_hash(new_password), session["user_id"])
                    )
                    new_version = cur.fetchone()[0]
                conn.commit()
                session["session_version"] = new_version
                send_password_changed_email(session["user_email"])
                success = "Password updated. You've been logged out of any other active sessions."
        finally:
            conn.close()

    return render_template("account-security.html", active_section="security",
                            breadcrumbs=[("Security", None)], error=error, success=success)


@app.route("/account/orders")
@login_required
def account_orders():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            rows, pagination = paginate_query(
                cur,
                "SELECT COUNT(*) FROM orders WHERE user_id = %s AND status = ANY(%s)",
                """
                SELECT id, items, total_aud, status, created_at FROM orders
                WHERE user_id = %s AND status = ANY(%s)
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                [session["user_id"], list(ACTIVE_STATUSES)],
                _current_page(),
            )
    finally:
        conn.close()

    orders = [{"id": r[0], "items": r[1], "total_aud": r[2], "status": r[3], "created_at": r[4].astimezone(SYDNEY_TZ)} for r in rows]
    return render_template("account-orders.html", active_section="orders", breadcrumbs=[("Orders", None)],
                            orders=orders, pagination=pagination, history=False)


@app.route("/account/orders/history")
@login_required
def account_orders_history():
    status_filter = request.args.get("status")
    date_from = _parse_date(request.args.get("from"))
    date_to = _parse_date(request.args.get("to"))
    order_number = request.args.get("q", "").strip()

    conditions = ["user_id = %s"]
    params = [session["user_id"]]

    if status_filter in HISTORY_STATUSES:
        conditions.append("status = %s")
        params.append(status_filter)
    else:
        conditions.append("status = ANY(%s)")
        params.append(list(HISTORY_STATUSES))

    if date_from:
        conditions.append("created_at >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("created_at < %s")
        params.append(date_to + timedelta(days=1))
    if order_number.isdigit():
        conditions.append("id = %s")
        params.append(int(order_number))

    where_clause = " AND ".join(conditions)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            rows, pagination = paginate_query(
                cur,
                f"SELECT COUNT(*) FROM orders WHERE {where_clause}",
                f"""
                SELECT id, items, total_aud, status, created_at FROM orders
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                params,
                _current_page(),
            )
    finally:
        conn.close()

    orders = [{"id": r[0], "items": r[1], "total_aud": r[2], "status": r[3], "created_at": r[4].astimezone(SYDNEY_TZ)} for r in rows]
    return render_template("account-orders.html", active_section="orders_history",
                            breadcrumbs=[("Orders", url_for("account_orders")), ("History", None)],
                            orders=orders, pagination=pagination, history=True,
                            status_filter=status_filter, date_from=request.args.get("from", ""),
                            date_to=request.args.get("to", ""), query=order_number)


@app.route("/account/orders/<int:order_id>")
@login_required
def account_order_detail(order_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, items, total_aud, status, created_at FROM orders WHERE id = %s AND user_id = %s",
                (order_id, session["user_id"])
            )
            row = cur.fetchone()
            if not row:
                return "Not found", 404

            activity_rows = get_activity(cur, "order", order_id, actions=("status_change",))
    finally:
        conn.close()

    order = {"id": row[0], "items": row[1], "total_aud": row[2], "status": row[3], "created_at": row[4].astimezone(SYDNEY_TZ)}
    timeline = [{"detail": a[1], "created_at": a[2].astimezone(SYDNEY_TZ)} for a in activity_rows]

    return render_template(
        "account-entity-detail.html", entity_type="order", entity=order,
        active_section="order_detail",
        breadcrumbs=[("Orders", url_for("account_orders")), (f"#{order_id}", None)],
        timeline=timeline, list_endpoint="account_orders_history",
    )


@app.route("/account/reservations")
@login_required
def account_reservations():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            rows, pagination = paginate_query(
                cur,
                "SELECT COUNT(*) FROM reservations WHERE user_id = %s AND status = ANY(%s)",
                """
                SELECT id, items, total_aud, status, pickup_date, notes, created_at FROM reservations
                WHERE user_id = %s AND status = ANY(%s)
                ORDER BY pickup_date ASC
                LIMIT %s OFFSET %s
                """,
                [session["user_id"], list(ACTIVE_STATUSES)],
                _current_page(),
            )
    finally:
        conn.close()

    reservations = [{
        "id": r[0], "items": r[1], "total_aud": r[2], "status": r[3],
        "pickup_date": r[4], "notes": r[5], "created_at": r[6].astimezone(SYDNEY_TZ)
    } for r in rows]
    return render_template("account-reservations.html", active_section="reservations",
                            breadcrumbs=[("Reservations", None)],
                            reservations=reservations, pagination=pagination, history=False)


@app.route("/account/reservations/history")
@login_required
def account_reservations_history():
    status_filter = request.args.get("status")
    date_from = _parse_date(request.args.get("from"))
    date_to = _parse_date(request.args.get("to"))
    reservation_number = request.args.get("q", "").strip()

    conditions = ["user_id = %s"]
    params = [session["user_id"]]

    if status_filter in HISTORY_STATUSES:
        conditions.append("status = %s")
        params.append(status_filter)
    else:
        conditions.append("status = ANY(%s)")
        params.append(list(HISTORY_STATUSES))

    if date_from:
        conditions.append("pickup_date >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("pickup_date <= %s")
        params.append(date_to)
    if reservation_number.isdigit():
        conditions.append("id = %s")
        params.append(int(reservation_number))

    where_clause = " AND ".join(conditions)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            rows, pagination = paginate_query(
                cur,
                f"SELECT COUNT(*) FROM reservations WHERE {where_clause}",
                f"""
                SELECT id, items, total_aud, status, pickup_date, notes, created_at FROM reservations
                WHERE {where_clause}
                ORDER BY pickup_date DESC
                LIMIT %s OFFSET %s
                """,
                params,
                _current_page(),
            )
    finally:
        conn.close()

    reservations = [{
        "id": r[0], "items": r[1], "total_aud": r[2], "status": r[3],
        "pickup_date": r[4], "notes": r[5], "created_at": r[6].astimezone(SYDNEY_TZ)
    } for r in rows]
    return render_template(
        "account-reservations.html", active_section="reservations_history",
        breadcrumbs=[("Reservations", url_for("account_reservations")), ("History", None)],
        reservations=reservations, pagination=pagination, history=True,
        status_filter=status_filter, date_from=request.args.get("from", ""),
        date_to=request.args.get("to", ""), query=reservation_number,
    )


@app.route("/account/reservations/<int:reservation_id>")
@login_required
def account_reservation_detail(reservation_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, items, total_aud, status, pickup_date, notes, created_at "
                "FROM reservations WHERE id = %s AND user_id = %s",
                (reservation_id, session["user_id"])
            )
            row = cur.fetchone()
            if not row:
                return "Not found", 404

            activity_rows = get_activity(cur, "reservation", reservation_id, actions=("status_change",))
    finally:
        conn.close()

    reservation = {
        "id": row[0], "items": row[1], "total_aud": row[2], "status": row[3],
        "pickup_date": row[4], "notes": row[5], "created_at": row[6].astimezone(SYDNEY_TZ)
    }
    timeline = [{"detail": a[1], "created_at": a[2].astimezone(SYDNEY_TZ)} for a in activity_rows]

    return render_template(
        "account-entity-detail.html", entity_type="reservation", entity=reservation,
        active_section="reservation_detail",
        breadcrumbs=[("Reservations", url_for("account_reservations")), (f"#{reservation_id}", None)],
        timeline=timeline, list_endpoint="account_reservations_history",
    )
