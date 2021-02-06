from flask import render_template,url_for,jsonify,request,flash,redirect,session,make_response,abort,current_app
from flaskserver import server,db,bcrypt,mail
from flaskserver.form import RegistrationForm,LoginForm,UpdateForm,ResetPasswordForm,ChangePasswordForm
from flaskserver.model import User,DayDataUsage,HourDataUsage
from flask_login import login_user,current_user,logout_user,login_required
from  collections import OrderedDict
from flask_mail import Message
import secrets 
import time
import os
import json
import re
from datetime import date,datetime
from threading import Thread

system_generated_code=None
movie_data=None
free_account_data_limit=1000
free_account='free'
multi_factor=3

class EmailThread(Thread):
	def __init__(self,func,email,code):
		super().__init__()
		self.func=func
		self.useremail=email
		self.code=code
	def run(self):
		with server.app_context():
			self.func(self.useremail,self.code)

class RemoveUserThread(Thread):
	def __init__(self,id):
		super().__init__()
		self.id=id
	def run(self):
		with server.app_context():
			user=User.query.filter_by(id=self.id).first()
			day_usages=DayDataUsage.query.filter_by(user_id=self.id).all()
			hour_usages=HourDataUsage.query.filter_by(user_id=self.id).all()
			db.session.delete(user)
			for day_usage in day_usages:
					db.session.delete(day_usage)	
			for hour_usage in hour_usages:
					db.session.delete(hour_usage)
			db.session.commit()



@server.route("/",methods=['GET'])
@server.route('/home',methods=['GET'])
def homePage():
	return render_template("home.html",about_activated=False,css_file=url_for('static',filename='style.css',q=time.time()),homePage=True)


def send_verify_code(email,code):
	msg=Message("One Time Verification Code",sender=server.config["MAIL_USERNAME"],recipients=[email])
	msg.body=f"""Your One Time Verification Code : {code}.
Please enter in your login page  to verify yourself."""
	mail.send(msg)

def send_resetpwd_code(email,code):
	msg=Message("Password Reset Verification Code",sender=server.config["MAIL_USERNAME"],recipients=[email])
	msg.body=f"""Your Passsword Reset Verification Code : {code}.
Please enter in your reset password page  to verify yourself."""
	mail.send(msg)

def removeUser():
	pass
	
	
def redirect_to_genapikey():
	flash("You have to register yourself, before login!","info")
	return redirect(url_for("generateApiKeyPage"))

@server.route("/generateapikey",methods=['GET','POST'])
def generateApiKeyPage():
	if current_user.is_authenticated:
		return redirect(url_for("homePage"))
	global system_generated_code
	form=RegistrationForm()
	if form.validate_on_submit():
		user_password=bcrypt.generate_password_hash(form.password.data).decode("utf-8")
		user_apikey=secrets.token_hex(14)
		user=User.query.filter_by(apikey=user_apikey).first()
		if user:
			user_apikey=secrets.token_hex(10)
		full_name=str(form.user_first_name.data).strip()+" "+str(form.user_last_name.data).strip()
		pwdlen=len(form.password.data)*multi_factor
		user=User(username=full_name,email=form.user_email.data,apikey=user_apikey,accounttype="free",password=user_password,
					regdate=datetime.strptime(datetime.now().strftime('%d%m%Y'),'%d%m%Y'),isverified=False,pwdlen=pwdlen)

		db.session.add(user)
		db.session.commit()
			# send a verification code to user gmail
		system_generated_code=secrets.token_hex(4)
		threaded_verify_code=EmailThread(send_verify_code,user.email,system_generated_code)
		threaded_verify_code.start()
		flash(f" A  Verification  Code  has been sent to: {form.user_email.data}",'success')
		res=make_response(redirect(url_for("login")))
		res.set_cookie(key='verified_user',value='false')
		return res
	return render_template("generate_api_key.html",title="Generate API Key",about_activated=True,form=form,css_file=url_for('static',filename='style.css',q=time.time()))

@server.route("/login",methods=["GET","POST"])
def login():
	global system_generated_code
	if current_user.is_authenticated:
		return redirect(url_for("homePage"))
	form=LoginForm()
	user=None
	user_verification_status=request.cookies.get('verified_user',False)
	if user_verification_status and user_verification_status.lower()=='true':
		user_verification_status=True
	else:
		user_verification_status=False
	if request.method=="POST" and request.form.get("submit",None)=='Resend':
		email_data=request.form['user_email']
		form.user_email.data=email_data
		user=User.query.filter_by(email=email_data).first()
		if user:
			system_generated_code=secrets.token_hex(4)
			threaded_verify_code=EmailThread(send_verify_code,user.email,system_generated_code)
			threaded_verify_code.start()
		else:
			flash("Please enter a registered email address, to get verification code!","alert")
			return redirect(url_for("login"))
	else:
		if form.validate_on_submit():
			user=User.query.filter_by(email=form.user_email.data).first()
			if user:
				verified_user=user.isverified
				if verified_user:
					if bcrypt.check_password_hash(user.password,form.password.data):
						flash("You have logged in successfully!","success")
						login_user(user)
						system_generated_code=None
						res=make_response(redirect(url_for('homePage')))
						res.set_cookie(key='verified_user',value='true')
						return res
					else:
						flash("Incorrect email or password!","alert")
						form.user_email.data=None

					
				else:
					try:
						if form.onetime_verification_code.data.lower()==system_generated_code.lower():
							user.isverified=True
							db.session.commit()
							if bcrypt.check_password_hash(user.password,form.password.data):
								flash("You have logged in successfully!","success")
								login_user(user)
								system_generated_code=None
								res=make_response(redirect(url_for('homePage')))
								res.set_cookie(key='verified_user',value='true')
								return res
							else:
								flash("Incorrect email or password!","alert")
								form.user_email.data=None

						else:
							flash("Please enter valid verification code!","alert")
							return redirect(url_for('login'))
					except AttributeError:
						if not system_generated_code:
							return redirect_to_genapikey()
			else:
				if system_generated_code:
					flash("Incorrect email or password!.", 'alert')
					form.user_email.data=None
				else:
					return redirect_to_genapikey()


	return render_template('login.html',title="Login",form=form,about_activated=True,
		                   verified_field_req=False if not system_generated_code else not user.isverified if user else not user_verification_status ,
		                   server=server,css_file=url_for('static',filename='style.css',q=time.time()))


@server.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('homePage'))

def fillDetails(ac_form,pwd_form):
	ac_form.user_email.data=current_user.email
	ac_form.user_first_name.data=str(current_user.username).split(' ')[0].capitalize()
	ac_form.user_last_name.data=str(current_user.username).split(' ')[1].capitalize()
	pwd_form.old_password.data="".join(['·']*(current_user.pwdlen//multi_factor))

@server.route('/account',methods=["GET","POST"])
@login_required
def account():
	account_form=UpdateForm()
	pwd_form=ChangePasswordForm()
	display=None
	if request.method =="POST" and request.form.get("update_acc",None):
		if account_form.validate_on_submit():
			full_name=str(account_form.user_first_name.data).strip().lower()+" "+str(account_form.user_last_name.data).strip().lower()
			current_user.username=full_name
			current_user.email=account_form.user_email.data
			db.session.commit()
			flash("Your account has been updated successfully!",'success')
			return redirect(url_for('account'))
	elif request.method=="POST" and request.form.get("change_pwd",None):
		display="block"
		fillDetails(account_form,pwd_form)
		if pwd_form.validate_on_submit():
			current_user.password=bcrypt.generate_password_hash(pwd_form.new_password.data).decode("utf-8")
			current_user.pwdlen=len(pwd_form.new_password.data)*multi_factor
			db.session.commit()
			flash("Your password has changed!",'success')
			return redirect(url_for('account'))
	elif request.method=='GET':
		fillDetails(account_form,pwd_form)
	return render_template('account.html',title='Account',acc_form=account_form,pwd_form=pwd_form,css_file=url_for('static',filename='style.css',q=time.time()),
							display=display)



def checkUserDataUsage(data_amount,user):
	day_data_usage=db.session.query(DayDataUsage).filter_by(user_id=user.id,usage_day=datetime.now().strftime('%Y-%m-%d')).first()
	if not day_data_usage:
		day_data_usage=DayDataUsage(daily_data_usage=data_amount,usage_day=datetime.strptime(datetime.now().strftime('%d%m%Y'),'%d%m%Y'),user_id=user.id)
		hour_data_usage=HourDataUsage(hourly_data_usage=data_amount,usage_hour=datetime.strptime(datetime.now().strftime("%I:00 %p"),"%I:00 %p"),
											usage_day=day_data_usage.usage_day,user_id=day_data_usage.user_id)
	else:
		hour_data_usage=HourDataUsage.query.filter_by(usage_hour=datetime.strptime(datetime.now().strftime("1900-01-01 %H:00:00"),"1900-01-01 %H:00:00"),
														user_id=day_data_usage.user_id).first()
		

		if hour_data_usage:
			hour_data_usage.hourly_data_usage+=data_amount

		else:
			hour_data_usage=HourDataUsage(hourly_data_usage=data_amount,usage_hour=datetime.strptime(datetime.now().strftime("%I:00 %p"),"%I:00 %p"),usage_day=day_data_usage.usage_day,
											user_id=day_data_usage.user_id)

		day_data_usage.daily_data_usage+=data_amount




	if day_data_usage.daily_data_usage >free_account_data_limit:
		return True
	
	db.session.add(day_data_usage)
	db.session.add(hour_data_usage)
	db.session.commit()
	return False


@server.route("/disneymovies/all/",methods=['GET'])
def allMovies():
	user_apikey=request.args.get('apikey').strip()
	user=User.query.filter_by(apikey=user_apikey).first()
	if user:
		file='movie_dataset.json'
		filename=os.path.join(server.root_path,'static/data',file)
		with open(filename,'r') as file:
			data=json.load(file)
		data_len=len(data["Movie Details"])
		limit_reached=checkUserDataUsage(data_len,user)
		if limit_reached:
			server_response={'Response':False,'Info':'Your request can not be processed, as it might exceed your daily limit.'}
		else:
			server_response={'Response':True,'Info':data}
		res=server.response_class(
			response=json.dumps(server_response),
			status=200,
			mimetype='application/json')
		return res
	else:
		data={'Response':False,'Info':'Invalid apikey.'}
		res=server.response_class(
			response=json.dumps(data),
			status=200,
			mimetype='application/json')
		return res

@server.route("/resetpassword",methods=["GET","POST"])
def resetPassword():
	global system_generated_code
	status=False
	form=ResetPasswordForm()
	if request.method=="POST":
		if request.form.get('verify_code',None):
			if system_generated_code:
				user_entered_code=request.form.get('verification_code',"")
				if user_entered_code!=system_generated_code:
					flash("Please enter valid verification code!","alert")
				else:
					status=True
					form.password.data=form.conform_password.data=status
			else:
				flash("To verify yourself, press 'Send/Resend Code' button!","info")

		elif request.form.get('send_code',None):
			user=User.query.filter_by(email=request.form["user_email"]).first()
			if user:
				system_generated_code=secrets.token_hex(4)
				threaded_verify_code=EmailThread(send_resetpwd_code,user.email,system_generated_code)
				threaded_verify_code.start()
			else:
				flash("Please enter a registered email address, to get verification code!","alert")
				return redirect(url_for("resetPassword"))
		elif request.form.get('reset_pwd',None):
				status=True
				if form.validate_on_submit():
					user=User.query.filter_by(email=request.form["user_email"]).first()
					if user:
						user.password=bcrypt.generate_password_hash(form.password.data).decode("utf-8")
						db.session.commit()
						flash("Your Password has been changed!","success")
						return redirect(url_for("login"))
					else:
						flash("Please enter a registered email address","alert")
						status=False

	form.verification_code.data=None
	return render_template('resetpwd.html',title="Reset Password",form=form,css_file=url_for('static',filename='style.css',q=time.time()),user_verified=status)





@server.route("/disneymovies/",methods=['GET'])
def selectedMovie():
	global movie_data
	user_apikey=request.args.get('apikey').strip()
	user=User.query.filter_by(apikey=user_apikey).first()
	if user:
		movie_title=request.args.get("title").strip().lower() if request.args.get("title") else None
		movie_year=request.args.get('year').strip() if request.args.get('year') else None
		imdb_id=request.args.get('id').strip() if request.args.get('id') else None
		if not movie_data:
			file='movie_dataset.json'
			filename=os.path.join(server.root_path,'static/data',file)
			with open(filename,'r') as file:
				movie_data=json.load(file)["Movie Details"]

		if movie_year:
			movie_list=list()
			try:
				server_response={"Response":False,"Info":"Invalid Year Value."}
				x=int(movie_year)

				if len(movie_year)==4:
					for movie in movie_data:
						patt=f"{movie_year}" 
						source=movie.get("Release date","") if movie.get("Release date","") else ""
						if re.search(patt,source):
							movie_list.append(movie)
					if movie_list:
						limit_reached=checkUserDataUsage(len(movie_list),user)
						if limit_reached:
							server_response={'Response':False,'Info':'Your request can not be processed, as it might exceed your daily limit.'}
						else:
							server_response={"Response":True,"Info":movie_list}
			except ValueError:
				pass

			res=server.response_class(
				response=json.dumps(server_response),
				status=200,
				mimetype="application/json")
			return res
		elif movie_title:
			movie=None
			for mov in movie_data:
				if str(mov["Title"]).lower()==movie_title:
					movie=mov.copy()
					break
			if movie:
				limit_reached=checkUserDataUsage(1,user)
				if limit_reached:
					server_response={'Response':False,'Info':'Your request can not be processed, as it might exceed your daily limit.'}
				else:
					server_response={"Response":True,"Info":movie}
			else:
				server_response={"Response":False,"Info":"Invalid Movie Title."}

			res=server.response_class(
				response=json.dumps(server_response),
				status=200,
				mimetype="application/json")
			return res

		elif imdb_id:
			movie=None
			for mov in movie_data:
				if mov["ImdbID"]==imdb_id:
					movie=mov.copy()
					break
			if movie:
				limit_reached=checkUserDataUsage(1,user)
				if limit_reached:
					server_response={'Response':False,'Info':'Your request can not be processed, as it might exceed your daily limit.'}
				else:
					server_response={"Response":True,"Info":movie}
			else:
				server_response={"Response":False,"Info":"Invalid IMDB ID."}

			res=server.response_class(
				response=json.dumps(server_response),
				status=200,
				mimetype="application/json")
			return res

		else:
			server_response={"Response":False,"Info":'Invalid Parameter or Value'}
			res=server.response_class(
				response=json.dumps(server_response),
				status=200,
				mimetype="application/json")
			return res
	else:
		data={'Response':False,'Info':'Invalid apikey'}
		res=server.response_class(
			response=json.dumps(data),
			status=200,
			mimetype='application/json')
		return res


@server.route("/apiusage",methods=["GET","POST"])
@login_required
def userApiUsage():
	date=datetime.now().strftime("%Y-%m-%d")
	if request.method=="POST":
		if request.is_json:
			date=request.get_json().strip('"')
			user_usage_data=dict()
			for data in HourDataUsage.query.filter_by(usage_day=date,user_id=current_user.id).all():
				user_usage_data[data.usage_hour.strftime("%I:00 %p")]=data.hourly_data_usage
			res=server.response_class(
				response=json.dumps(user_usage_data),
				status=200,
				mimetype='application/json',
				headers={" Access-Control-Allow-Credentials":True})

			return res

	return render_template("apiusage.html",title="Api Usage",dayUsage=DayDataUsage,hourUsage=HourDataUsage,css_file=url_for('static',filename='style.css',q=time.time()),
							server=request.base_url,date=date,free_account_limit=free_account_data_limit)



@server.route("/delacc",methods=["POST"])
@login_required
def delAcc():
	threaded_code=RemoveUserThread(current_user.id)
	threaded_code.start()
	return redirect(url_for("homePage"))
@server.errorhandler(404)
def error_404(e):
	return render_template('error_404.html',css_file=url_for('static',filename='style.css',q=time.time()),error_msg=str(e)),404

@server.errorhandler(401)
def error_401(e):
	return render_template('error_401.html',css_file=url_for('static',filename='style.css',q=time.time()),error_msg=str(e)),401

@server.errorhandler(403)
def error_403(e):
	return render_template('error_403.html',css_file=url_for('static',filename='style.css',q=time.time()),error_msg=str(e)),403

@server.errorhandler(500)
def error_500(e):
	return render_template('error_500.html',css_file=url_for('static',filename='style.css',q=time.time()),error_msg=str(e)),500


	
	