from datetime import datetime

import requests

from .config import EXCHANGE_API_KEY, SYDNEY_TZ

currencies = [
    {"code": "USD", "name": "United States Dollar", "flag": "us", "margin": 0.02, "denominations": [1, 5, 10, 20, 50, 100]},
    {"code": "GBP", "name": "British Pound Sterling", "flag": "gb", "margin": 0.02, "denominations": [5, 10, 20, 50]},
    {"code": "EUR", "name": "Euro", "flag": "eu", "margin": 0.02, "denominations": [5, 10, 20, 50, 100]},
    {"code": "JPY", "name": "Japanese Yen", "flag": "jp", "margin": 4, "denominations": [1000, 2000, 5000, 10000]},
    {"code": "HKD", "name": "Hong Kong Dollar", "flag": "hk", "margin": 0.2, "denominations": [10, 20, 50, 100, 500, 1000]},
    {"code": "THB", "name": "Thai Baht", "flag": "th", "margin": 1.5, "denominations": [20, 50, 100, 500, 1000]},
    {"code": "SGD", "name": "Singapore Dollar", "flag": "sg", "margin": 0.04, "denominations": [2, 5, 10, 50, 100]},
    {"code": "NZD", "name": "New Zealand Dollar", "flag": "nz", "margin": 0.04, "denominations": [5, 10, 20, 50, 100]},
    {"code": "FJD", "name": "Fijian Dollar", "flag": "fj", "margin": 0.8, "denominations": [5, 10, 20, 50, 100]},
    {"code": "CNY", "name": "Chinese Yuan", "flag": "cn", "margin": 0.2, "denominations": [1, 5, 10, 20, 50, 100]},
    {"code": "CAD", "name": "Canadian Dollar", "flag": "ca", "margin": 0.04, "denominations": [5, 10, 20, 50, 100]},
    {"code": "IDR", "name": "Indonesian Rupiah", "flag": "id", "margin": 900, "denominations": [1000, 2000, 5000, 10000, 20000, 50000, 100000]},
    {"code": "PHP", "name": "Philippine Peso", "flag": "ph", "margin": 3.5, "denominations": [20, 50, 100, 200, 500, 1000]},
    {"code": "INR", "name": "Indian Rupee", "flag": "in", "margin": 5.5, "denominations": [10, 20, 50, 100, 200, 500]},
    {"code": "AED", "name": "United Arab Emirates Dirham", "flag": "ae", "margin": 0.2, "denominations": [5, 10, 20, 50, 100, 200, 500]},
    {"code": "KRW", "name": "South Korean Won", "flag": "kr", "margin": 90, "denominations": [1000, 5000, 10000, 50000]},
    {"code": "MYR", "name": "Malaysian Ringgit", "flag": "my", "margin": 0.2, "denominations": [1, 5, 10, 20, 50, 100]},
    {"code": "ZAR", "name": "South African Rand", "flag": "za", "margin": 0, "denominations": [10, 20, 50, 100, 200]},
    {"code": "VND", "name": "Vietnamese Dong", "flag": "vn", "margin": 1500, "denominations": [10000, 20000, 50000, 100000, 200000, 500000]},
    {"code": "TWD", "name": "New Taiwan Dollar", "flag": "tw", "margin": 2, "denominations": [100, 200, 500, 1000]},
    {"code": "CHF", "name": "Swiss Franc", "flag": "ch", "margin": 0.022, "denominations": [10, 20, 50, 100, 200]},
    {"code": "TRY", "name": "Turkish Lira", "flag": "tr", "margin": 3.5, "denominations": [5, 10, 20, 50, 100, 200]},
    {"code": "XPF", "name": "CFP Franc", "flag": "pf", "margin": 0, "denominations": [500, 1000, 5000, 10000]},
    {"code": "DKK", "name": "Danish Krone", "flag": "dk", "margin": 0, "denominations": [50, 100, 200, 500, 1000]},
    {"code": "SEK", "name": "Swedish Krona", "flag": "se", "margin": 0, "denominations": [20, 50, 100, 200, 500]},
    {"code": "CZK", "name": "Czech Koruna", "flag": "cz", "margin": 0, "denominations": [100, 200, 500, 1000, 2000]},
    {"code": "PLN", "name": "Polish Zloty", "flag": "pl", "margin": 0, "denominations": [10, 20, 50, 100, 200]},
    {"code": "HUF", "name": "Hungarian Forint", "flag": "hu", "margin": 0, "denominations": [500, 1000, 2000, 5000, 10000]},
    {"code": "MXN", "name": "Mexican Peso", "flag": "mx", "margin": 0, "denominations": [20, 50, 100, 200, 500]},
    {"code": "VUV", "name": "Vanuatu Vatu", "flag": "vu", "margin": 0, "denominations": [500, 1000, 2000, 5000, 10000]},
    {"code": "NOK", "name": "Norwegian Krone", "flag": "no", "margin": 0, "denominations": [50, 100, 200, 500, 1000]},
    {"code": "AUD", "name": "Australian Dollar", "flag": "au", "margin": 0, "denominations": [0.01, 1, 100]}
]

EXCHANGE_RATE_URL = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest/AUD"


def find_currency(code):
    return next((c for c in currencies if c["code"] == code), None)


def fetch_exchange_rate():
    try:
        response = requests.get(EXCHANGE_RATE_URL, timeout=10)
        response.raise_for_status()

        data = response.json()
        all_rates = data["conversion_rates"]

        current_time = datetime.now(SYDNEY_TZ).strftime('%Y-%m-%d %H:%M:%S')
        for currency in currencies:
            code = currency["code"]
            raw_rate = all_rates.get(code)
            # Fallback to None if code isn't found
            currency["rate"] = raw_rate - currency["margin"] if raw_rate is not None else None
            print(f"[{current_time}] Updated {code}: {currency['rate']}")

    except requests.exceptions.RequestException as e:
        current_time = datetime.now(SYDNEY_TZ).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{current_time}] API Request failed: {e}")
