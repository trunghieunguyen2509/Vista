from flask import Flask, render_template, jsonify
import requests
import time

# Initialize flask applkication
app = Flask(__name__)

# 1. Define the currency list data
currencies = [
        {"code": "USD", "flag": "us"},
        {"code": "GBP", "flag": "gb"},
        {"code": "EUR", "flag": "eu"},
        {"code": "JPY", "flag": "jp"},
        {"code": "HKD", "flag": "hk"},
        {"code": "THB", "flag": "th"},
        {"code": "SGD", "flag": "sg"},
        {"code": "NZD", "flag": "nz"},
        {"code": "FJD", "flag": "fj"},
        {"code": "CNY", "flag": "cn"},
        {"code": "CAD", "flag": "ca"},
        {"code": "IDR", "flag": "id"},
        {"code": "PHP", "flag": "ph"},
        {"code": "INR", "flag": "in"},
        {"code": "AED", "flag": "ae"},
        {"code": "KRW", "flag": "kr"},
        {"code": "MYR", "flag": "my"},
        {"code": "ZAR", "flag": "za"},
        {"code": "VND", "flag": "vn"},
        {"code": "TWD", "flag": "tw"},
        {"code": "CHF", "flag": "ch"},
        {"code": "TRY", "flag": "tr"},
        {"code": "XPF", "flag": "pf"},
        {"code": "DKK", "flag": "dk"},
        {"code": "SEK", "flag": "se"},
        {"code": "CZK", "flag": "cz"},
        {"code": "PLN", "flag": "pl"},
        {"code": "HUF", "flag": "hu"},
        {"code": "MXN", "flag": "mx"},
        {"code": "VUV", "flag": "vu"},
        {"code": "NOK", "flag": "no"},
        {"code": "AUD", "flag": "au"}
    ]

# Define route
@app.route("/")
def index():
    return render_template('index.html', currencies=currencies)

@app.route("/buy-currency")
def buy_currency():
    return render_template('buy-currency.html', currencies=currencies)
if __name__ == '__main__':
    app.run(debug=True)
