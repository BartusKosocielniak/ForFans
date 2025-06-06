from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User
from .forms import LoginForm, RegisterForm
from flask import current_app as app

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
            exception = 'Użytkownik z takim emailem już istnieje.'
            return render_template('register.html', register_form=form, title="Rejestracja", header="Dołącz do nas!",
                                   exception='Użytkownik z takim emailem już istnieje.')

        role = 'admin' if User.query.count() == 0 else 'user'
        hashed_pw = generate_password_hash(form.user_password.data)
        new_user = User(
            username=form.username.data,
            first_name=form.user_first_name.data,
            last_name=form.user_last_name.data,
            email=form.user_email.data,
            password=hashed_pw,
            role=role
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Rejestracja zakończona sukcesem. Zaloguj się.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', register_form=form, title="Rejestracja", header="Dołącz do nas!", exception="")


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


# admin endpoint

@app.route("/users")
@login_required  # tylko zalogowani
def show_users():
    if current_user.role != 'admin':
        abort(403)  # Forbidden
    users = User.query.all()
    return render_template("users.html", users=users)