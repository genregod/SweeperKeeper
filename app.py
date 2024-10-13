from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager
from models import User, Casino, Account
from forms import RegistrationForm, LoginForm, AddCasinoForm, AddAccountForm
from coin_claimer import CoinClaimer
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sweeper_keeper.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager.init_app(app)

coin_claimer = CoinClaimer()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_casinos = Casino.query.filter_by(user_id=current_user.id).all()
    user_accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', casinos=user_casinos, accounts=user_accounts)

@app.route('/add_casino', methods=['GET', 'POST'])
@login_required
def add_casino():
    form = AddCasinoForm()
    if form.validate_on_submit():
        new_casino = Casino(name=form.name.data, website=form.website.data, user_id=current_user.id)
        db.session.add(new_casino)
        db.session.commit()
        flash('New casino added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_casino.html', form=form)

@app.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    form = AddAccountForm()
    form.casino.choices = [(c.id, c.name) for c in Casino.query.filter_by(user_id=current_user.id).all()]
    if form.validate_on_submit():
        new_account = Account(username=form.username.data, casino_id=form.casino.data, user_id=current_user.id)
        db.session.add(new_account)
        db.session.commit()
        flash('New account added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_account.html', form=form)

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
    app.run(host='0.0.0.0', port=8080, debug=True)
