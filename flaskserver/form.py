import email_validator
from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,TextAreaField,RadioField,PasswordField
from wtforms.validators import DataRequired,Email,Length,EqualTo,ValidationError
from flaskserver.model import User
from flask_login import current_user


class RegistrationForm(FlaskForm):
	user_email=StringField("Email",validators=[DataRequired(),Email()])
	user_full_name=StringField('UserName')
	user_first_name=StringField('',validators=[DataRequired(),Length(min=2,max=10)])
	user_last_name=StringField('',validators=[DataRequired(),Length(min=2,max=10)])
	password=PasswordField("Password",validators=[DataRequired()])
	conform_password=PasswordField("Confrom Password",validators=[DataRequired(),EqualTo('password')])
	submit=SubmitField("Sign Up")
	user_name=None

	def validate_user_email(self,useremail):
		user=User.query.filter_by(email=useremail.data).first()
		if user:
			raise ValidationError('User with given email exist. ')


	def validate_user_full_name(self,user_full_name):
		print(self.user_first_name.data,self.user_last_name.data,not (self.user_first_name.data!="" or self.user_last_name.data!="")  )
		if not (self.user_first_name.data!="" or self.user_last_name.data!="") :
			raise ValidationError("Please fill Name Field.")
		else:
			username=self.user_first_name.data+" "+self.user_last_name.data 
			user=User.query.filter_by(username=username).first()
			if user:
				raise ValidationError("User with give name exist.")


class LoginForm(FlaskForm):
	user_email=StringField("Email",validators=[DataRequired(),Email()])
	password=PasswordField("Password")
	onetime_verification_code=StringField("Verification Code")
	submit=SubmitField("Login In")
	user_name=None


class UpdateForm(FlaskForm):
	user_email=StringField("Email",validators=[DataRequired(),Email()])
	user_first_name=StringField('First Name',validators=[DataRequired(),Length(min=2,max=30)])
	user_last_name=StringField('Last Name',validators=[DataRequired(),Length(min=2,max=20)])
	update_acc=SubmitField('Update')
	username=None

	def validate_user_email(self,user_email):
		if current_user.email!=user_email.data:
			user=User.query.filter_by(email=user_email.data).first()
			if user:
				raise ValidationError('User with given email exist. ')

	def validate_user_first_name(self,user_first_name):
		self.username=str(user_first_name.data).strip().lower()

	def validate_user_last_name(self,user_last_name):
		self.username+=(' '+str(user_last_name.data).strip().lower())
		if self.username!=current_user.username:
			user=User.query.filter_by(username=self.username).first()
			if user:
				raise ValidationError("User with give name exist.")


class ChangePasswordForm(FlaskForm):
	old_password=StringField("Old Password")
	new_password=PasswordField("New Password",validators=[Length(min=6)])
	new_confrm_password=PasswordField("Conform New Password",validators=[Length(min=6),EqualTo("new_password",message="Both Passwords must match.")])
	change_pwd=SubmitField("Update Password")



class ResetPasswordForm(FlaskForm):
	user_email=StringField("Email",validators=[DataRequired(),Email()])
	verification_code=StringField("Verification Code")
	password=PasswordField("Password")
	conform_password=PasswordField("Confrom Password")
	reset_pwd=SubmitField("Reset Password")
	verify_code=SubmitField("Verify")
	send_code=SubmitField("Send/Resend Code")

	def validate_conform_password(self,conform_password):
		if conform_password.data :
			if self.password.data!=conform_password.data:
				raise ValidationError("Field must be equal to password.")
		else:
			raise ValidationError("The field is required.")

	def validate_password(self,password):
		if not self.password.data:
			raise ValidationError("The field is required.")




