from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
bootstrap = Bootstrap(app)

class LoginForm(FlaskForm):
    user_email = StringField('Email', validators=[DataRequired(), Email()])
    user_password = PasswordField('Hasło', validators=[DataRequired()])
    submit = SubmitField('Zaloguj')

class RegisterForm(FlaskForm):
    user_first_name = StringField('Imię', validators=[DataRequired()])
    user_last_name = StringField('Nazwisko', validators=[DataRequired()])
    user_email = StringField('Email', validators=[DataRequired(), Email()])
    user_password = PasswordField('Hasło', validators=[DataRequired()])
    submit = SubmitField('Zarejestruj')

@app.route('/')
def login():
    form = LoginForm()
    return render_template('login.html', login_form=form, title="Logowanie", header="Witaj!")

@app.route('/register')
def register():
    form = RegisterForm()
    return render_template('register.html', register_form=form, title="Rejestracja", header="Dołącz do nas!")

@app.route('/home')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
    