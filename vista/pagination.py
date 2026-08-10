PAGE_SIZE = 10


def paginate_query(cur, count_sql, list_sql, params, page):
    """Runs count_sql to get the total, clamps `page` into range, then runs
    list_sql (which must end with `LIMIT %s OFFSET %s`) for that page.
    Returns (rows, pagination_info)."""
    cur.execute(count_sql, params)
    total = cur.fetchone()[0]
    total_pages = max((total + PAGE_SIZE - 1) // PAGE_SIZE, 1)
    page = min(max(page, 1), total_pages)
    offset = (page - 1) * PAGE_SIZE

    cur.execute(list_sql, params + [PAGE_SIZE, offset])
    rows = cur.fetchall()

    return rows, {
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }
