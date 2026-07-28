from flask import Flask, render_template, jsonify
import requests
import time
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler


# Initialize flask applkication
app = Flask(__name__)

# 1. Define the currency list data
currencies = [
    {"code": "USD", "name": "United States Dollar", "flag": "us", "margin": 0},
    {"code": "GBP", "name": "British Pound Sterling", "flag": "gb", "margin": 0},
    {"code": "EUR", "name": "Euro", "flag": "eu", "margin": 0},
    {"code": "JPY", "name": "Japanese Yen", "flag": "jp", "margin": 0},
    {"code": "HKD", "name": "Hong Kong Dollar", "flag": "hk", "margin": 0},
    {"code": "THB", "name": "Thai Baht", "flag": "th", "margin": 0},
    {"code": "SGD", "name": "Singapore Dollar", "flag": "sg", "margin": 0},
    {"code": "NZD", "name": "New Zealand Dollar", "flag": "nz", "margin": 0},
    {"code": "FJD", "name": "Fijian Dollar", "flag": "fj", "margin": 0},
    {"code": "CNY", "name": "Chinese Yuan", "flag": "cn", "margin": 0},
    {"code": "CAD", "name": "Canadian Dollar", "flag": "ca", "margin": 0},
    {"code": "IDR", "name": "Indonesian Rupiah", "flag": "id", "margin": 0},
    {"code": "PHP", "name": "Philippine Peso", "flag": "ph", "margin": 0},
    {"code": "INR", "name": "Indian Rupee", "flag": "in", "margin": 0},
    {"code": "AED", "name": "United Arab Emirates Dirham", "flag": "ae", "margin": 0},
    {"code": "KRW", "name": "South Korean Won", "flag": "kr", "margin": 0},
    {"code": "MYR", "name": "Malaysian Ringgit", "flag": "my", "margin": 0},
    {"code": "ZAR", "name": "South African Rand", "flag": "za", "margin": 0},
    {"code": "VND", "name": "Vietnamese Dong", "flag": "vn", "margin": 0},
    {"code": "TWD", "name": "New Taiwan Dollar", "flag": "tw", "margin": 0},
    {"code": "CHF", "name": "Swiss Franc", "flag": "ch", "margin": 0},
    {"code": "TRY", "name": "Turkish Lira", "flag": "tr", "margin": 0},
    {"code": "XPF", "name": "CFP Franc", "flag": "pf", "margin": 0},
    {"code": "DKK", "name": "Danish Krone", "flag": "dk", "margin": 0},
    {"code": "SEK", "name": "Swedish Krona", "flag": "se", "margin": 0},
    {"code": "CZK", "name": "Czech Koruna", "flag": "cz", "margin": 0},
    {"code": "PLN", "name": "Polish Zloty", "flag": "pl", "margin": 0},
    {"code": "HUF", "name": "Hungarian Forint", "flag": "hu", "margin": 0},
    {"code": "MXN", "name": "Mexican Peso", "flag": "mx", "margin": 0},
    {"code": "VUV", "name": "Vanuatu Vatu", "flag": "vu", "margin": 0},
    {"code": "NOK", "name": "Norwegian Krone", "flag": "no", "margin": 0},
    {"code": "AUD", "name": "Australian Dollar", "flag": "au", "margin": 0}
]

#Handle API
load_dotenv()
api_key = os.getenv("EXCHANGE_API_KEY")
url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/AUD"
# Extract the conversion rates



def fetch_exchange_rate():
    try:
        # Get data from API
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # 2. Parse JSON body
        data = response.json()
        all_rates = data["conversion_rates"]
        
        # 3. Update currencies list
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        for currency in currencies:
            code = currency["code"]
            # Fallback to None if code isn't found
            currency["rate"] = all_rates.get(code) 
            print(f"[{current_time}] Updated {code}: {currency['rate']}")

    except requests.exceptions.RequestException as e:
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{current_time}] API Request failed: {e}")

# Define route
@app.route("/")
def index():
    return render_template('index.html', currencies=currencies)

@app.route("/buy-currency")
def buy_currency():
    return render_template('buy-currency.html', currencies=currencies)

if __name__ == '__main__':
    # Fetch the rate immediately
    fetch_exchange_rate()
    #Start background scheduler run on a separate thread so it doesn't block Flask
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_exchange_rate, 'interval', hours = 2)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler.start()
    app.run(debug=True)
    


