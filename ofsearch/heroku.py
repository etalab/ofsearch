from flask import Flask
from werkzeug.contrib.fixers import ProxyFix

from .api import api
from .database import DB, DEFAULT_INDEX
from .utils import ObjectDict

config = ObjectDict(verbose=False, index=DEFAULT_INDEX)
db = DB(config)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config.SWAGGER_UI_DOC_EXPANSION = 'list'

api.init_app(app)
db.init_app(app)
