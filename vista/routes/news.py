from datetime import datetime

from flask import render_template

from .. import app
from ..config import SYDNEY_TZ
from ..db import get_db_connection


def _relative_time(published_at):
    if not published_at:
        return "Recently"

    now = datetime.now(SYDNEY_TZ)
    seconds = (now - published_at.astimezone(SYDNEY_TZ)).total_seconds()

    if seconds < 60:
        return "Just now"

    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"

    hours = int(minutes // 60)
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"

    days = int(hours // 24)
    if days < 7:
        return f"{days} day{'s' if days != 1 else ''} ago"

    return published_at.astimezone(SYDNEY_TZ).strftime('%Y-%m-%d')


@app.route("/news")
def news():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT title, summary, source, url, published_at, fetched_at
                FROM aud_news
                ORDER BY COALESCE(published_at, fetched_at) DESC
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    news_items = [{
        "title": row[0],
        "summary": row[1],
        "source": row[2],
        "url": row[3],
        "relative_time": _relative_time(row[4] or row[5])
    } for row in rows]

    return render_template("news.html", news_items=news_items)
