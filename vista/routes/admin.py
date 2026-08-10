from flask import flash, redirect, render_template, request, url_for

from .. import app
from ..activity import get_activity
from ..admin_entities import add_entity_note, assign_entity, update_entity_status
from ..config import SYDNEY_TZ
from ..db import get_db_connection
from ..decorators import admin_required, super_admin_required
from ..pagination import paginate_query

RESERVATION_SORT_COLUMNS = {
    "pickup_date": "r.pickup_date",
    "created_at": "r.created_at",
    "total_aud": "r.total_aud",
}
ORDER_SORT_COLUMNS = {
    "created_at": "o.created_at",
    "total_aud": "o.total_aud",
}


def _staff_options(cur):
    cur.execute("SELECT id, email FROM users WHERE role IN ('staff', 'admin') ORDER BY email")
    return [{"id": row[0], "email": row[1]} for row in cur.fetchall()]


@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM reservations WHERE status = 'pending'")
            pending_reservations = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
            pending_orders = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM reservations WHERE created_at >= now() - interval '7 days'")
            new_reservations_7d = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM orders WHERE created_at >= now() - interval '7 days'")
            new_orders_7d = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(total_aud), 0) FROM orders WHERE created_at >= date_trunc('month', now())")
            revenue_month = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE role IN ('staff', 'admin')")
            staff_count = cur.fetchone()[0]

            cur.execute("""
                SELECT a.entity_type, a.entity_id, a.action, a.detail, a.created_at, u.email
                FROM admin_activity_log a
                LEFT JOIN users u ON u.id = a.actor_user_id
                ORDER BY a.created_at DESC
                LIMIT 15
            """)
            activity_rows = cur.fetchall()
    finally:
        conn.close()

    recent_activity = [{
        "entity_type": row[0], "entity_id": row[1], "action": row[2], "detail": row[3],
        "created_at": row[4].astimezone(SYDNEY_TZ), "actor_email": row[5]
    } for row in activity_rows]

    return render_template(
        "admin-dashboard.html",
        active_section="dashboard", breadcrumbs=[("Dashboard", None)],
        pending_reservations=pending_reservations,
        pending_orders=pending_orders,
        new_reservations_7d=new_reservations_7d,
        new_orders_7d=new_orders_7d,
        revenue_month=revenue_month,
        staff_count=staff_count,
        recent_activity=recent_activity,
    )


@app.route("/admin/staff", methods=["GET", "POST"])
@super_admin_required
def admin_staff():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role")
        if role not in ("customer", "staff", "admin"):
            error = "Invalid role."
        else:
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("UPDATE users SET role = %s WHERE email = %s", (role, email))
                    if cur.rowcount == 0:
                        error = f'No account found for "{email}".'
                    else:
                        conn.commit()
                        flash(f'{email} is now {role}.', 'success')
            finally:
                conn.close()

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, email, role, created_at FROM users
                WHERE role IN ('staff', 'admin')
                ORDER BY role, email
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    staff_members = [{
        "id": row[0], "email": row[1], "role": row[2], "created_at": row[3].astimezone(SYDNEY_TZ)
    } for row in rows]

    return render_template(
        "admin-staff.html", active_section="staff", breadcrumbs=[("Staff", None)],
        staff_members=staff_members, error=error,
    )


@app.route("/admin/reservations")
@admin_required
def admin_reservations():
    status_filter = request.args.get("status")
    query = request.args.get("q", "").strip()
    sort = RESERVATION_SORT_COLUMNS.get(request.args.get("sort"), "r.pickup_date")
    direction = "DESC" if request.args.get("dir") == "desc" else "ASC"

    conditions = []
    params = []
    if status_filter in ("pending", "fulfilled", "cancelled"):
        conditions.append("r.status = %s")
        params.append(status_filter)
    if query:
        conditions.append("u.email ILIKE %s")
        params.append(f"%{query}%")
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            rows, pagination = paginate_query(
                cur,
                f"SELECT COUNT(*) FROM reservations r JOIN users u ON u.id = r.user_id {where_clause}",
                f"""
                SELECT r.id, u.email, r.items, r.total_aud, r.pickup_date, r.status, r.created_at, a.email
                FROM reservations r
                JOIN users u ON u.id = r.user_id
                LEFT JOIN users a ON a.id = r.assigned_to
                {where_clause}
                ORDER BY {sort} {direction}
                LIMIT %s OFFSET %s
                """,
                params, page,
            )
    finally:
        conn.close()

    reservations = [{
        "id": row[0], "email": row[1], "items": row[2], "total_aud": row[3],
        "pickup_date": row[4], "status": row[5], "created_at": row[6].astimezone(SYDNEY_TZ),
        "assignee_email": row[7]
        } for row in rows]
    return render_template(
        "admin-reservations.html", active_section="reservations", breadcrumbs=[("Reservations", None)],
        reservations=reservations, pagination=pagination,
        status_filter=status_filter, query=query,
        sort=request.args.get("sort"), dir=request.args.get("dir"),
    )


@app.route("/admin/reservations/<int:reservation_id>")
@admin_required
def admin_reservation_detail(reservation_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.id, u.email, r.items, r.total_aud, r.pickup_date, r.status, r.created_at, a.email, r.notes
                FROM reservations r
                JOIN users u ON u.id = r.user_id
                LEFT JOIN users a ON a.id = r.assigned_to
                WHERE r.id = %s
            """, (reservation_id,))
            row = cur.fetchone()
            if not row:
                return "Not found", 404

            staff = _staff_options(cur)
            activity_rows = get_activity(cur, "reservation", reservation_id)
    finally:
        conn.close()

    reservation = {
        "id": row[0], "email": row[1], "items": row[2], "total_aud": row[3],
        "pickup_date": row[4], "status": row[5], "created_at": row[6].astimezone(SYDNEY_TZ),
        "assignee_email": row[7], "notes": row[8]
    }
    activity = [{
        "action": a[0], "detail": a[1], "created_at": a[2].astimezone(SYDNEY_TZ), "actor_email": a[3]
    } for a in activity_rows]

    return render_template(
        "admin-entity-detail.html", entity=reservation, entity_type="reservation",
        active_section="reservation_detail",
        breadcrumbs=[("Reservations", url_for("admin_reservations")), (f"#{reservation_id}", None)],
        activity=activity, staff=staff, list_endpoint="admin_reservations",
        status_url=url_for("admin_reservation_status", reservation_id=reservation_id),
        assign_url=url_for("admin_reservation_assign", reservation_id=reservation_id),
        note_url=url_for("admin_reservation_note", reservation_id=reservation_id),
    )


@app.route("/admin/reservations/<int:reservation_id>/status", methods=["POST"])
@admin_required
def admin_reservation_status(reservation_id):
    new_status = request.form.get("status")
    update_entity_status("reservations", "reservation", reservation_id, new_status)
    flash(f"Status updated to {new_status}.", "success")
    return redirect(url_for("admin_reservation_detail", reservation_id=reservation_id))


@app.route("/admin/reservations/<int:reservation_id>/assign", methods=["POST"])
@admin_required
def admin_reservation_assign(reservation_id):
    assignee_id = request.form.get("assigned_to") or None
    assign_entity("reservations", "reservation", reservation_id, int(assignee_id) if assignee_id else None)
    flash("Assignment updated.", "success")
    return redirect(url_for("admin_reservation_detail", reservation_id=reservation_id))


@app.route("/admin/reservations/<int:reservation_id>/note", methods=["POST"])
@admin_required
def admin_reservation_note(reservation_id):
    add_entity_note("reservation", reservation_id, request.form.get("note"))
    flash("Note added.", "success")
    return redirect(url_for("admin_reservation_detail", reservation_id=reservation_id))


@app.route("/admin/orders")
@admin_required
def admin_orders():
    status_filter = request.args.get("status")
    query = request.args.get("q", "").strip()
    sort = ORDER_SORT_COLUMNS.get(request.args.get("sort"), "o.created_at")
    direction = "DESC" if request.args.get("dir") != "asc" else "ASC"

    conditions = []
    params = []
    if status_filter in ("pending", "fulfilled", "cancelled"):
        conditions.append("o.status = %s")
        params.append(status_filter)
    if query:
        conditions.append("u.email ILIKE %s")
        params.append(f"%{query}%")
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            rows, pagination = paginate_query(
                cur,
                f"SELECT COUNT(*) FROM orders o JOIN users u ON u.id = o.user_id {where_clause}",
                f"""
                SELECT o.id, u.email, o.items, o.total_aud, o.status, o.created_at, a.email
                FROM orders o
                JOIN users u ON u.id = o.user_id
                LEFT JOIN users a ON a.id = o.assigned_to
                {where_clause}
                ORDER BY {sort} {direction}
                LIMIT %s OFFSET %s
                """,
                params, page,
            )
    finally:
        conn.close()

    orders = [{
        "id": row[0], "email": row[1], "items": row[2], "total_aud": row[3],
        "status": row[4], "created_at": row[5].astimezone(SYDNEY_TZ), "assignee_email": row[6]
        } for row in rows]
    return render_template(
        "admin-orders.html", active_section="orders", breadcrumbs=[("Orders", None)],
        orders=orders, pagination=pagination,
        status_filter=status_filter, query=query,
        sort=request.args.get("sort"), dir=request.args.get("dir"),
    )


@app.route("/admin/orders/<int:order_id>")
@admin_required
def admin_order_detail(order_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.id, u.email, o.items, o.total_aud, o.status, o.created_at, a.email
                FROM orders o
                JOIN users u ON u.id = o.user_id
                LEFT JOIN users a ON a.id = o.assigned_to
                WHERE o.id = %s
            """, (order_id,))
            row = cur.fetchone()
            if not row:
                return "Not found", 404

            staff = _staff_options(cur)
            activity_rows = get_activity(cur, "order", order_id)
    finally:
        conn.close()

    order = {
        "id": row[0], "email": row[1], "items": row[2], "total_aud": row[3],
        "status": row[4], "created_at": row[5].astimezone(SYDNEY_TZ), "assignee_email": row[6]
    }
    activity = [{
        "action": a[0], "detail": a[1], "created_at": a[2].astimezone(SYDNEY_TZ), "actor_email": a[3]
    } for a in activity_rows]

    return render_template(
        "admin-entity-detail.html", entity=order, entity_type="order",
        active_section="order_detail",
        breadcrumbs=[("Orders", url_for("admin_orders")), (f"#{order_id}", None)],
        activity=activity, staff=staff, list_endpoint="admin_orders",
        status_url=url_for("admin_order_status", order_id=order_id),
        assign_url=url_for("admin_order_assign", order_id=order_id),
        note_url=url_for("admin_order_note", order_id=order_id),
    )


@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def admin_order_status(order_id):
    new_status = request.form.get("status")
    update_entity_status("orders", "order", order_id, new_status)
    flash(f"Status updated to {new_status}.", "success")
    return redirect(url_for("admin_order_detail", order_id=order_id))


@app.route("/admin/orders/<int:order_id>/assign", methods=["POST"])
@admin_required
def admin_order_assign(order_id):
    assignee_id = request.form.get("assigned_to") or None
    assign_entity("orders", "order", order_id, int(assignee_id) if assignee_id else None)
    flash("Assignment updated.", "success")
    return redirect(url_for("admin_order_detail", order_id=order_id))


@app.route("/admin/orders/<int:order_id>/note", methods=["POST"])
@admin_required
def admin_order_note(order_id):
    add_entity_note("order", order_id, request.form.get("note"))
    flash("Note added.", "success")
    return redirect(url_for("admin_order_detail", order_id=order_id))
