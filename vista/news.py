import re
from calendar import timegm
from datetime import datetime, timezone

import feedparser

from .config import SYDNEY_TZ
from .db import get_db_connection

NEWS_FEEDS = [
    ("FXStreet", "https://www.fxstreet.com/rss/news"),
    ("Investing.com", "https://www.investing.com/rss/news_1.rss"),
    ("Yahoo Finance", "https://feeds.finance.yahoo.com/rss/2.0/headline?s=AUDUSD=X&region=US&lang=en-US"),
]

NEWS_KEYWORDS = ["aud", "australian dollar", "rba", "reserve bank of australia"]

MAX_STORED_ITEMS = 20
SUMMARY_MAX_LENGTH = 280

_TAG_RE = re.compile(r"<[^>]+>")


def _clean_summary(raw_summary):
    text = _TAG_RE.sub("", raw_summary or "").strip()
    if len(text) > SUMMARY_MAX_LENGTH:
        text = text[:SUMMARY_MAX_LENGTH].rsplit(" ", 1)[0] + "…"
    return text


def _is_aud_related(title, summary):
    haystack = f"{title} {summary}".lower()
    return any(keyword in haystack for keyword in NEWS_KEYWORDS)


def _parse_published_at(entry):
    struct = entry.get("published_parsed")
    if not struct:
        return None
    return datetime.fromtimestamp(timegm(struct), tz=timezone.utc)


def fetch_aud_news():
    current_time = datetime.now(SYDNEY_TZ).strftime('%Y-%m-%d %H:%M:%S')
    candidates = []
    seen_titles = set()

    for source_name, feed_url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(feed_url, request_headers={"User-Agent": "Mozilla/5.0"})
            for entry in feed.entries:
                title = (entry.get("title") or "").strip()
                link = entry.get("link")
                if not title or not link:
                    continue

                summary = _clean_summary(entry.get("summary"))
                if not _is_aud_related(title, summary):
                    continue

                title_key = title.lower()
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)

                candidates.append({
                    "title": title,
                    "summary": summary,
                    "source": source_name,
                    "url": link,
                    "published_at": _parse_published_at(entry),
                })
            print(f"[{current_time}] Fetched {len(feed.entries)} items from {source_name}")
        except Exception as e:
            print(f"[{current_time}] AUD news fetch failed for {source_name}: {e}")

    if not candidates:
        return

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for item in candidates:
                cur.execute(
                    """
                    INSERT INTO aud_news (title, summary, source, url, published_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                    """,
                    (item["title"], item["summary"], item["source"], item["url"], item["published_at"])
                )
            cur.execute("""
                DELETE FROM aud_news
                WHERE id NOT IN (
                    SELECT id FROM aud_news
                    ORDER BY COALESCE(published_at, fetched_at) DESC
                    LIMIT %s
                )
            """, (MAX_STORED_ITEMS,))
        conn.commit()
    finally:
        conn.close()

    print(f"[{current_time}] AUD news updated: {len(candidates)} matching items processed")
