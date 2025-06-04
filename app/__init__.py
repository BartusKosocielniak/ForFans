from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "MesGQOn2VI"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, '../data/users.sqlite')

    db.init_app(app)
    login_manager.init_app(app)
    # bootstrap = Bootstrap(app)

    Bootstrap(app)

    with app.app_context():
        from . import routes, models
        db.create_all()

    return app
