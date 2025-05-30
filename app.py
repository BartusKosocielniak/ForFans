from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# MODELE
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(10), default='user')  # admin / user

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# FORMY
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

# ROUTY
@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.user_email.data).first()
        if user and check_password_hash(user.password, form.user_password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Błędny email lub hasło')
    return render_template('login.html', login_form=form, title="Logowanie", header="Witaj!")

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.user_email.data).first()
        if existing_user:
            flash('Użytkownik z takim emailem już istnieje.')
            return redirect(url_for('register'))

        role = 'admin' if User.query.count() == 0 else 'user'  # Pierwszy user to admin
        hashed_pw = generate_password_hash(form.user_password.data)
        new_user = User(
            first_name=form.user_first_name.data,
            last_name=form.user_last_name.data,
            email=form.user_email.data,
            password=hashed_pw,
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Rejestracja zakończona sukcesem. Zaloguj się.')
        return redirect(url_for('login'))

    return render_template('register.html', register_form=form, title="Rejestracja", header="Dołącz do nas!")

@app.route('/home')
@login_required
def home():
    return render_template('home.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Zostałeś wylogowany.')
    return redirect(url_for('login'))

# Inicjalizacja bazy jeśli nie istnieje
if not os.path.exists('users.db'):
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
