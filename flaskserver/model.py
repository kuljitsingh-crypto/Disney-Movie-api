from datetime import datetime
from flaskserver import db
from  flaskserver import login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


class User(db.Model,UserMixin):
	__tablename__='user'
	id=db.Column(db.Integer,primary_key=True)
	username=db.Column(db.String(50),nullable=False)
	email=db.Column(db.String(120),nullable=False,unique=True)
	apikey=db.Column(db.String(60),unique=True,nullable=False)
	accounttype=db.Column(db.String(40),nullable=False,default='Free')
	isverified=db.Column(db.Boolean,nullable=False,default=False)
	password=db.Column(db.String(60),nullable=False)
	regdate=db.Column(db.Date,nullable=False)
	pwdlen=db.Column(db.Integer,nullable=False)
	month_usage=db.relationship("DayDataUsage",backref='user',lazy=True)

	def __repr__(self):
		return f"User({self.username},{self.email},{self.apikey},{self.accounttype},{self.isverified},{self.id},{self.regdate})"

class DayDataUsage(db.Model):
	__tablename__='daydatausage'
	id=db.Column(db.Integer,primary_key=True)
	daily_data_usage=db.Column(db.Integer ,nullable=False,default=0)
	usage_day=db.Column(db.Date,nullable=False)
	user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
	hour_usage=db.relationship("HourDataUsage",backref='daydatausage',lazy=True)

	def __repr__(self):
		return f"DayDataUsage({self.daily_data_usage},{self.usage_day},{self.user_id})"


class HourDataUsage(db.Model):
	__tablename__='hourdatausage'
	id=db.Column(db.Integer,primary_key=True)
	hourly_data_usage=db.Column(db.Integer,nullable=False,default=0)
	usage_hour=db.Column(db.DateTime,nullable=False)
	usage_day=db.Column(db.Date,nullable=False)
	user_id=db.Column(db.Integer,db.ForeignKey('daydatausage.user_id'),nullable=False)

	def __repr__(self):
		return f"HourDataUsage({self.hourly_data_usage},{self.usage_hour},{self.usage_day},{self.user_id})"
