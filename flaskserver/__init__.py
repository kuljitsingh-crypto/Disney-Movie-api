from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
import os


server=Flask(__name__)
server.config['SECRET_KEY']='fa1530c2cb7bdf2c425a7e3dc87439c6'
server.config["SQLALCHEMY_DATABASE_URI"]='sqlite:///user.db?check_same_thread=False'
db=SQLAlchemy(server)
db.init_app(server)
bcrypt=Bcrypt(server)
login_manager=LoginManager(server)
login_manager.login_view='login'
login_manager.login_message_category = "info"
server.config["MAIL_SERVER"]="smtp.gmail.com"
server.config["MAIL_PORT"]=587
server.config["MAIL_USE_TLS"]=True
server.config["MAIL_USERNAME"]=os.environ["EmailName"]
server.config["MAIL_PASSWORD"]=os.environ["EmailPassword"]
mail=Mail(server)

from flaskserver import routes