from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
import os
import logging
from coin_claimer import CoinClaimer
from analytics import Analytics
from datetime import timedelta
from flask_migrate import Migrate
from models import db, User, Casino, Account

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///sweeper_keeper.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

coin_claimer = CoinClaimer()
analytics = Analytics()

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already exists.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    logger.debug('Registration endpoint accessed')
    
    if current_user.is_authenticated:
        logger.debug('Authenticated user attempted to access registration page')
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if request.method == 'POST':
        logger.debug('Registration form submitted')
        
        if form.validate_on_submit():
            logger.debug('Form validation successful')
            try:
                new_user = User(
                    username=form.username.data,
                    email=form.email.data,
                    password_hash=generate_password_hash(form.password.data, method='sha256')
                )
                db.session.add(new_user)
                db.session.commit()
                logger.info(f'New user registered successfully: {form.username.data}')
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            
            except Exception as e:
                logger.error(f'Error during user registration: {str(e)}')
                db.session.rollback()
                flash('An error occurred during registration. Please try again.', 'danger')
                return render_template('register.html', form=form)
        else:
            logger.debug('Form validation failed')
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
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
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    success = coin_claimer.claim_coins(account_id)
    if success:
        account.coins += 100
        db.session.commit()
        return jsonify({"success": True, "message": "Coins claimed successfully"})
    return jsonify({"success": False, "message": "Failed to claim coins"}), 500

@app.route('/analytics')
@login_required
def analytics_dashboard():
    total_coins = analytics.get_total_coins_claimed(current_user.id)
    success_rate = analytics.get_claim_success_rate(current_user.id)
    coins_by_casino = analytics.get_coins_claimed_by_casino(current_user.id)
    claim_history = analytics.get_claim_history(current_user.id)

    last_24h_coins = analytics.get_total_coins_claimed(current_user.id, timedelta(hours=24))
    last_7d_coins = analytics.get_total_coins_claimed(current_user.id, timedelta(days=7))
    last_30d_coins = analytics.get_total_coins_claimed(current_user.id, timedelta(days=30))

    return render_template('analytics.html',
                        total_coins=total_coins,
                        success_rate=success_rate,
                        coins_by_casino=coins_by_casino,
                        claim_history=claim_history,
                        last_24h_coins=last_24h_coins,
                        last_7d_coins=last_7d_coins,
                        last_30d_coins=last_30d_coins)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    if os.environ.get('FLASK_ENV') == 'production':
        from load_balancer import LoadBalancer
        load_balancer = LoadBalancer(app)
        load_balancer.start()
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)
