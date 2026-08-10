def log_activity(cur, entity_type, entity_id, actor_user_id, action, detail=None):
    cur.execute(
        """
        INSERT INTO admin_activity_log (entity_type, entity_id, actor_user_id, action, detail)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (entity_type, entity_id, actor_user_id, action, detail)
    )


def get_activity(cur, entity_type, entity_id, actions=None):
    if actions:
        cur.execute("""
            SELECT a.action, a.detail, a.created_at, u.email
            FROM admin_activity_log a
            LEFT JOIN users u ON u.id = a.actor_user_id
            WHERE a.entity_type = %s AND a.entity_id = %s AND a.action = ANY(%s)
            ORDER BY a.created_at DESC
        """, (entity_type, entity_id, list(actions)))
    else:
        cur.execute("""
            SELECT a.action, a.detail, a.created_at, u.email
            FROM admin_activity_log a
            LEFT JOIN users u ON u.id = a.actor_user_id
            WHERE a.entity_type = %s AND a.entity_id = %s
            ORDER BY a.created_at DESC
        """, (entity_type, entity_id))
    return cur.fetchall()
