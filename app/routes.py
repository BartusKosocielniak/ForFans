from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, admin_required
from .forms import LoginForm, RegisterForm
from flask import current_app as app
from flask import request, jsonify

@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.user_email.data).first()
        if user and check_password_hash(user.password, form.user_password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Incorrect password or email')
    return render_template('login.html', login_form=form, title="Sign in", header="Hello!")

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(
            email=form.user_email.data,
            username=form.username.data
        ).first()
        if existing_user:
            return render_template('register.html', register_form=form, title="Sing up", header="Dołącz do nas!",
                                   exception='A user with that email or username already exists.')

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
        flash('Sign up success. Sign in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', register_form=form, title="Sign up", header="Join us", exception="")


@app.route('/home')
@login_required
def home():
    return render_template('home.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You just sign out')
    return redirect(url_for('login'))


# admin endpoint

@app.route("/users")
@login_required  # tylko zalogowani
@admin_required
def show_users():
    # if current_user.role != 'admin':
    #     abort(403)  # Forbidden
    users = User.query.all()
    return render_template("users.html", users=users)


# @app.route('/update_user', methods=['POST'])
# def update_user():
#     if request.is_json:
#         data = request.get_json()
#         try:
#             user = User.query.get_or_404(data['user_id'])
#             user.username = data['username']
#             user.first_name = data['first_name']
#             user.last_name = data['last_name']
#             user.email = data['email']
#             user.role = data['role']
#             db.session.commit()
#             return jsonify({'success': True})
#         except Exception as e:
#             return jsonify({'success': False, 'error': str(e)})
#     return jsonify({'success': False, 'error': 'Invalid request'})
#

#
@app.route('/update_user', methods=['POST'])
@login_required
@admin_required
def update_user():
    data = request.get_json()
    user_id = data.get('user_id')
    username = data.get('username')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    role = data.get('role')

    # Przykład walidacji
    if not all([user_id, username, email, role, first_name, last_name]):
        return jsonify({'success': False, 'error': 'Wypełnij wszystkie wymagane pola'}), 400

    # Aktualizacja w bazie danych (przykład z SQLAlchemy)
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Użytkownik nie istnieje'}), 404

    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.role = role
    db.session.commit()

    return jsonify({'success': True})

@app.route('/delete/<int:user_id>', methods=['DELETE'])
@login_required
def delete(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'User not found'}), 404
