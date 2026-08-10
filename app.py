import os

from apscheduler.schedulers.background import BackgroundScheduler

from vista import app
from vista.config import DEBUG
from vista.currencies import fetch_exchange_rate
from vista.db import init_db
from vista.news import fetch_aud_news

init_db()
fetch_exchange_rate()
fetch_aud_news()

if not DEBUG or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_exchange_rate, 'interval', hours=1)
    scheduler.add_job(fetch_aud_news, 'interval', hours=24)
    scheduler.start()

if __name__ == '__main__':
    app.run(debug=DEBUG)
