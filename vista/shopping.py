from flask import session

from .currencies import find_currency


def get_session_list_view(session_key):
    raw_items = session.get(session_key, [])
    items = []
    total_aud = 0
    for i, item in enumerate(raw_items):
        currency = find_currency(item["code"])
        if not currency or not currency.get("rate"):
            continue
        aud_cost = item["amount"] / currency["rate"]
        total_aud += aud_cost
        items.append({
            "index": i,
            "code": currency["code"],
            "name": currency["name"],
            "flag": currency["flag"],
            "amount": item["amount"],
            "rate": currency["rate"],
            "aud_cost": aud_cost
        })
    return items, total_aud


def add_session_item(session_key, code, amount):
    if find_currency(code) and amount and amount > 0:
        items = session.get(session_key, [])
        items.append({"code": code, "amount": amount})
        session[session_key] = items


def remove_session_item(session_key, index):
    items = session.get(session_key, [])
    if 0 <= index < len(items):
        items.pop(index)
        session[session_key] = items
