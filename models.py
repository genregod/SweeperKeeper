from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    casinos = db.relationship('Casino', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Casino(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    last_collection = db.Column(db.DateTime, default=datetime.utcnow)
    next_collection = db.Column(db.DateTime)
    collection_interval = db.Column(db.Integer, default=24)  # in hours
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def update_next_collection(self):
        self.next_collection = self.last_collection + timedelta(hours=self.collection_interval)
