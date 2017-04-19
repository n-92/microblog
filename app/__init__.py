from flask import Flask
from .config import *
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_openid import OpenID
from .config import basedir


app=Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
oid = OpenID(app, os.path.join(basedir, 'tmp'))
lm.init_app(app)
lm.login_view = 'login'
from app import views,models
