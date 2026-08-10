from flask import session

from .activity import log_activity
from .db import get_db_connection

VALID_STATUSES = ("pending", "fulfilled", "cancelled")
_VALID_TABLES = {"reservations", "orders"}


def _check_table(table):
    if table not in _VALID_TABLES:
        raise ValueError(f"invalid table: {table}")


def update_entity_status(table, entity_type, entity_id, new_status):
    _check_table(table)
    if new_status not in VALID_STATUSES:
        return
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT status FROM {table} WHERE id = %s", (entity_id,))
            row = cur.fetchone()
            if not row:
                return
            old_status = row[0]
            cur.execute(f"UPDATE {table} SET status = %s WHERE id = %s", (new_status, entity_id))
            if old_status != new_status:
                log_activity(cur, entity_type, entity_id, session.get("user_id"),
                             "status_change", f"{old_status} → {new_status}")
        conn.commit()
    finally:
        conn.close()


def assign_entity(table, entity_type, entity_id, assignee_id):
    _check_table(table)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            assignee_email = None
            if assignee_id:
                cur.execute("SELECT email FROM users WHERE id = %s", (assignee_id,))
                assignee_row = cur.fetchone()
                assignee_email = assignee_row[0] if assignee_row else None
            cur.execute(f"UPDATE {table} SET assigned_to = %s WHERE id = %s", (assignee_id, entity_id))
            detail = f"Assigned to {assignee_email}" if assignee_email else "Unassigned"
            log_activity(cur, entity_type, entity_id, session.get("user_id"), "assignment", detail)
        conn.commit()
    finally:
        conn.close()


def add_entity_note(entity_type, entity_id, note_text):
    if not note_text or not note_text.strip():
        return
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            log_activity(cur, entity_type, entity_id, session.get("user_id"), "note", note_text.strip())
        conn.commit()
    finally:
        conn.close()
