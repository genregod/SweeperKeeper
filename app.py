from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from coin_claimer import CoinClaimer

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sweeper_keeper.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

coin_claimer = CoinClaimer()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    casinos = db.relationship('Casino', backref='user', lazy=True)
    accounts = db.relationship('Account', backref='user', lazy=True)

class Casino(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    casino_id = db.Column(db.Integer, db.ForeignKey('casino.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    casino = db.relationship('Casino', backref='accounts')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        new_user = User(username=username, password=generate_password_hash(password, method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    casinos = Casino.query.filter_by(user_id=current_user.id).all()
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', casinos=casinos, accounts=accounts)

@app.route('/add_casino', methods=['GET', 'POST'])
@login_required
def add_casino():
    if request.method == 'POST':
        name = request.form.get('name')
        website = request.form.get('website')
        new_casino = Casino(name=name, website=website, user_id=current_user.id)
        db.session.add(new_casino)
        db.session.commit()
        flash('Casino added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_casino.html')

@app.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    if request.method == 'POST':
        username = request.form.get('username')
        casino_id = request.form.get('casino')
        new_account = Account(username=username, casino_id=casino_id, user_id=current_user.id)
        db.session.add(new_account)
        db.session.commit()
        flash('Account added successfully!', 'success')
        return redirect(url_for('dashboard'))
    casinos = Casino.query.filter_by(user_id=current_user.id).all()
    return render_template('add_account.html', casinos=casinos)

@app.route('/claim_coins/<int:account_id>')
@login_required
def claim_coins(account_id):
    account = Account.query.get_or_404(account_id)
    if account.user_id != current_user.id:
        flash('You are not authorized to claim coins for this account.', 'danger')
        return redirect(url_for('dashboard'))
    
    success = coin_claimer.claim_coins(account_id)
    if success:
        flash('Coins claimed successfully!', 'success')
    else:
        flash('Failed to claim coins. Please try again later.', 'danger')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
