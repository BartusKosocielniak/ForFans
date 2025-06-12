from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, admin_required, Post, Follow
from .forms import LoginForm, RegisterForm, UpdateAccountForm, PostForm
from flask import current_app as app
from flask import request, jsonify

from .utils import save_picture  # jeśli masz osobny plik


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.user_email.data).first()
        if user and check_password_hash(user.password, form.user_password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Incorrect password or email', 'danger')
    return render_template('login.html', login_form=form, title="Sign in", header="Hello!")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_email = User.query.filter_by(email=form.user_email.data).first()
        existing_username = User.query.filter_by(username=form.username.data).first()

        if existing_email:
            flash('An account with this email already exists.', 'danger')
            return redirect(url_for('register'))

        if existing_username:
            flash('An account with this username already exists.', 'danger')
            return redirect(url_for('register'))

        role = 'admin' if User.query.count() == 0 else 'user'
        hashed_pw = generate_password_hash(form.user_password.data)

        new_user = User(
            username=form.username.data,
            first_name=form.user_first_name.data,
            last_name=form.user_last_name.data,
            email=form.user_email.data,
            password=hashed_pw,
            role=role,
            description="empty"
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Sign up success. Sign in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', register_form=form, title="Sign up", header="Join us")


@app.route('/home')
@login_required
def home():
    posts = Post.get_random_posts()
    return render_template('home.html', user=current_user, posts=posts)


@app.route("/search_users")
@login_required
def search_users():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    results = User.query.filter(
        db.or_(
            User.username.ilike(f"%{query}%"),
            User.first_name.ilike(f"%{query}%"),
            User.last_name.ilike(f"%{query}%")
        )
    ).limit(10).all()

    users = [
        {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
        for user in results
    ]
    return jsonify(users)


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
    return render_template("users.html", users=users, user=current_user)


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
@app.route('/update_user_by_id', methods=['POST'])
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
    description = data.get('description')

    # Przykład walidacji
    if not all([user_id, username, email, role, first_name, last_name]):
        return jsonify({'success': False, 'error': 'Fill all required parameters'}), 400

    # Aktualizacja w bazie danych (przykład z SQLAlchemy)
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User doesnt exist'}), 404

    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.role = role
    user.description = description
    db.session.commit()

    return jsonify({'success': True})


@app.route('/delete/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'User not found'}), 404


@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def show_user(user_id):
    # Post.query.get_or_404(post_id)
    show_user = User.query.get_or_404(user_id)
    is_following = False
    # show_user = User.query.filter_by(id=user_id).all()
    posts = Post.query.filter_by(author=show_user) \
        .order_by(Post.date_posted.desc()) \
        .all()
    if current_user.id == user_id or current_user.role == 'admin':
        return render_template("profile_self.html", show_user=show_user, user=current_user, posts=posts)
    if current_user.id != user_id:
        is_following = current_user.is_following(show_user)
        return render_template("profile_view.html", show_user=show_user, user=current_user, posts=posts, is_following=is_following)
    return None


@app.route("/user/<int:user_id>/edit", methods=['GET', 'POST'])
@login_required
def account(user_id):
    if current_user.id == user_id or current_user.role == 'admin':
        users = User.query.filter_by(id=user_id).all()
        form = UpdateAccountForm()
        if form.validate_on_submit():
            # Obsługa zdjęcia
            if form.picture.data:
                picture_file = save_picture(form.picture.data)
                users[0].image_file = picture_file

            # Aktualizacja danych
            users[0].username = form.username.data
            users[0].first_name = form.user_first_name.data
            users[0].last_name = form.user_last_name.data
            users[0].email = form.user_email.data
            users[0].description = form.description.data

            db.session.commit()
            flash('Profile has changed!', 'success')
            return redirect(url_for('show_user', user_id=users[0].id))

        elif request.method == 'GET':
            # Wstępne uzupełnienie formularza
            form.username.data = users[0].username
            form.user_first_name.data = users[0].first_name
            form.user_last_name.data = users[0].last_name
            form.user_email.data = users[0].email
            form.description.data = users[0].description

        image_file = url_for('static', filename='uploads/' + users[0].image_file)
        return render_template('profile_edit.html',
                               title='Moje konto',
                               image_file=image_file,
                               form=form,
                               user=current_user)  # Dodaj to
    return None


@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            author=current_user
        )
        db.session.add(post)
        db.session.commit()
        flash('Your post uploaded!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form)


@app.route('/post/<int:post_id>')
@login_required
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post, user=current_user)

@app.route('/posts')
@login_required
@admin_required
def all_posts():
    search_query = request.args.get('q', '').strip()

    if search_query:
        posts = Post.query.filter(
            or_(
                Post.title.ilike(f'%{search_query}%'),
                Post.content.ilike(f'%{search_query}%'),
                User.username.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        posts = Post.query.all()
    return render_template('posts.html', user=current_user, posts=posts)

@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your profile updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='edit post', form=form)

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Post has deleted!', 'success')
    return redirect(url_for('home'))

@app.route('/toggle_follow/<int:user_id>', methods=['POST'])
@login_required
def toggle_follow(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cant follow yourself!", "warning")
        return redirect(url_for('view_profile', user_id=user_id))

    if current_user.is_following(user):
        follow = Follow.query.filter_by(follower_id=current_user.id, followed_id=user.id).first()
        db.session.delete(follow)
        flash("Unfollow user", "info")
    else:
        follow = Follow(follower_id=current_user.id, followed_id=user.id)
        db.session.add(follow)
        flash("Follow user", "success")

    db.session.commit()
    return redirect(url_for('show_user', user_id=user_id))


