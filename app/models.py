from datetime import datetime, timezone
from functools import wraps

from flask import abort
from sqlalchemy.sql.functions import random

from . import db
from flask_login import UserMixin, current_user
from . import login_manager


class Follow(db.Model):
    """Tabela pośrednicząca dla relacji obserwowania między użytkownikami"""
    __tablename__ = 'follow'

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Relacje z użyciem back_populates (bardziej czytelne)
    follower = db.relationship(
        'User',
        foreign_keys=[follower_id],
        back_populates='following_relations'
    )
    followed = db.relationship(
        'User',
        foreign_keys=[followed_id],
        back_populates='follower_relations'
    )


class User(UserMixin, db.Model):

    """Model użytkownika"""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(10), default='user')#creator, admin, user
    description = db.Column(db.String(200))
    image_file = db.Column(db.String(120), nullable=False, default='default.jpg')  # <- ścieżka
    # posts = db.relationship('Post', backref='author', lazy=True)

    # Relacje dla obserwowania
    following_relations = db.relationship(
        'Follow',
        foreign_keys=[Follow.follower_id],
        back_populates='follower',
        cascade='all, delete-orphan'
    )

    follower_relations = db.relationship(
        'Follow',
        foreign_keys=[Follow.followed_id],
        back_populates='followed',
        cascade='all, delete-orphan'
    )

    # Wygodne metody do obsługi obserwowanych
    @property
    def following(self):
        """Lista użytkowników, których obserwuje obecny użytkownik"""
        return [rel.followed for rel in self.following_relations]

    @property
    def followers(self):
        """Lista użytkowników obserwujących obecnego użytkownika"""
        return [rel.follower for rel in self.follower_relations]

    def follow(self, user):
        """Obserwuj innego użytkownika"""
        if not self.is_following(user):
            rel = Follow(follower=self, followed=user)
            db.session.add(rel)
            db.session.commit()

    def unfollow(self, user):
        """Przestań obserwować użytkownika"""
        rel = Follow.query.filter_by(
            follower_id=self.id,
            followed_id=user.id
        ).first()
        if rel:
            db.session.delete(rel)
            db.session.commit()

    def is_following(self, user):
        """Sprawdź czy obserwuje innego użytkownika"""
        return Follow.query.filter_by(
            follower_id=self.id,
            followed_id=user.id
        ).count() > 0

    def is_followed_by(self, user):
        """Sprawdź czy jest obserwowany przez użytkownika"""
        return Follow.query.filter_by(
            follower_id=user.id,
            followed_id=self.id
        ).count() > 0



class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc) )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('posts', lazy=True))

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

    def get_random_posts(limit=10):
        posts = Post.query.all()
        if len(posts) <= limit:
            return posts
        return random.sample(posts, limit)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function