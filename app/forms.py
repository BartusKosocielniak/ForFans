from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    user_email = StringField('Email', validators=[DataRequired(), Email()])
    user_password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign in')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    user_first_name = StringField('First name', validators=[DataRequired()])
    user_last_name = StringField('Last name', validators=[DataRequired()])
    user_email = StringField('Email', validators=[DataRequired(), Email()])
    user_password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign up')
