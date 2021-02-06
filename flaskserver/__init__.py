from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flaskserver.config import Config
import os

app=Flask(__name__)

db=SQLAlchemy()
bcrypt=Bcrypt()
login_manager=LoginManager()
login_manager.login_view='login'
login_manager.login_message_category = "info"

mail=Mail()


def create_app(config_class=Config):
	app.config.from_object(Config)

	db.init_app(app)
	login_manager.init_app(app)
	mail.init_app(app)
	bcrypt.init_app(app)
	with app.app_context():
		from flaskserver import routes
		db.create_all()


	return app


