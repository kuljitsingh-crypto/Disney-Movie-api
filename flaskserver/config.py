import os

class Config():
	SECRET_KEY='fa1530c2cb7bdf2c425a7e3dc87439c6'
	SQLALCHEMY_DATABASE_URI='sqlite:///user.db?check_same_thread=False'
	MAIL_SERVER="smtp.gmail.com"
	MAIL_PORT=587
	MAIL_USE_TLS=True
	MAIL_USERNAME=os.environ["EmailName"]
	MAIL_PASSWORD=os.environ["EmailPassword"]