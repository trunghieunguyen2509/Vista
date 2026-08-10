import os

from flask import Flask

from .config import SECRET_KEY

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(_BASE_DIR, "templates"),
    static_folder=os.path.join(_BASE_DIR, "static"),
)
app.secret_key = SECRET_KEY

# Imported for their side effect of registering routes on `app`. Must come
# after `app` is defined above, since each routes module does `from .. import app`.
from .routes import account, admin, auth, cart, main, news, reserve  # noqa: E402,F401
