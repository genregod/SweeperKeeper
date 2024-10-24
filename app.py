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
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from time import sleep

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')

db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
    db_url += '?sslmode=require'

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///sweeper_keeper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_timeout': 30,
    'pool_recycle': 1800,
    'max_overflow': 5,
    'pool_pre_ping': True,
}

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

coin_claimer = CoinClaimer()
analytics = Analytics()

def retry_db_operation(operation, max_retries=3, delay=1):
    last_error = None
    for attempt in range(max_retries):
        try:
            return operation()
        except OperationalError as e:
            last_error = e
            if "SSL connection has been closed" in str(e):
                logger.warning(f"SSL connection error on attempt {attempt + 1}/{max_retries}, retrying...")
                sleep(delay * (2 ** attempt))
            else:
                raise
    raise last_error

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), 
                                             EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate_username(self, field):
        def check_username():
            return User.query.filter_by(username=field.data).first()
        if retry_db_operation(check_username):
            raise ValidationError('Username already exists.')

    def validate_email(self, field):
        def check_email():
            return User.query.filter_by(email=field.data).first()
        if retry_db_operation(check_email):
            raise ValidationError('Email already registered.')

@login_manager.user_loader
def load_user(user_id):
    def get_user():
        return User.query.get(int(user_id))
    return retry_db_operation(get_user)

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
                def create_user():
                    new_user = User(
                        username=form.username.data,
                        email=form.email.data,
                        password_hash=generate_password_hash(form.password.data, method='sha256')
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    return new_user

                retry_db_operation(create_user)
                logger.info(f'New user registered successfully: {form.username.data}')
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            
            except OperationalError as e:
                logger.error(f'Database connection error during registration: {str(e)}')
                db.session.rollback()
                flash('A database connection error occurred. Please try again.', 'danger')
            except SQLAlchemyError as e:
                logger.error(f'Database error during registration: {str(e)}')
                db.session.rollback()
                flash('An error occurred during registration. Please try again.', 'danger')
            except Exception as e:
                logger.error(f'Unexpected error during registration: {str(e)}')
                db.session.rollback()
                flash('An unexpected error occurred. Please try again.', 'danger')
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
        def authenticate_user():
            user = User.query.filter_by(username=form.username.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                return user
            return None

        try:
            user = retry_db_operation(authenticate_user)
            if user:
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            flash('Invalid username or password', 'danger')
        except OperationalError:
            flash('A database error occurred. Please try again.', 'danger')
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
    def get_user_data():
        casinos = Casino.query.filter_by(user_id=current_user.id).all()
        accounts = Account.query.filter_by(user_id=current_user.id).all()
        return casinos, accounts
    
    try:
        casinos, accounts = retry_db_operation(get_user_data)
        return render_template('dashboard.html', casinos=casinos, accounts=accounts)
    except OperationalError:
        flash('Unable to load dashboard data. Please try again.', 'danger')
        return redirect(url_for('index'))

@app.route('/add_casino', methods=['GET', 'POST'])
@login_required
def add_casino():
    if request.method == 'POST':
        def create_casino():
            new_casino = Casino(name=request.form.get('name'), 
                              website=request.form.get('website'), 
                              user_id=current_user.id)
            db.session.add(new_casino)
            db.session.commit()
        
        try:
            retry_db_operation(create_casino)
            flash('Casino added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except OperationalError:
            flash('Failed to add casino. Please try again.', 'danger')
    return render_template('add_casino.html')

@app.route('/add_account', methods=['GET', 'POST'])
@login_required
def add_account():
    if request.method == 'POST':
        def create_account():
            new_account = Account(username=request.form.get('username'),
                                casino_id=request.form.get('casino'),
                                user_id=current_user.id)
            db.session.add(new_account)
            db.session.commit()
        
        try:
            retry_db_operation(create_account)
            flash('Account added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except OperationalError:
            flash('Failed to add account. Please try again.', 'danger')

    def get_casinos():
        return Casino.query.filter_by(user_id=current_user.id).all()
    
    try:
        casinos = retry_db_operation(get_casinos)
        return render_template('add_account.html', casinos=casinos)
    except OperationalError:
        flash('Unable to load casino data. Please try again.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/claim_coins/<int:account_id>')
@login_required
def claim_coins(account_id):
    def process_claim():
        account = Account.query.get_or_404(account_id)
        if account.user_id != current_user.id:
            return jsonify({"success": False, "message": "Unauthorized"}), 403
        
        success = coin_claimer.claim_coins(account_id)
        if success:
            account.coins += 100
            db.session.commit()
            return jsonify({"success": True, "message": "Coins claimed successfully"})
        return jsonify({"success": False, "message": "Failed to claim coins"}), 500
    
    try:
        return retry_db_operation(process_claim)
    except OperationalError:
        return jsonify({"success": False, "message": "Database error occurred"}), 500

@app.route('/analytics')
@login_required
def analytics_dashboard():
    def get_analytics_data():
        total_coins = analytics.get_total_coins_claimed(current_user.id)
        success_rate = analytics.get_claim_success_rate(current_user.id)
        coins_by_casino = analytics.get_coins_claimed_by_casino(current_user.id)
        claim_history = analytics.get_claim_history(current_user.id)
        last_24h_coins = analytics.get_total_coins_claimed(current_user.id, timedelta(hours=24))
        last_7d_coins = analytics.get_total_coins_claimed(current_user.id, timedelta(days=7))
        last_30d_coins = analytics.get_total_coins_claimed(current_user.id, timedelta(days=30))
        return (total_coins, success_rate, coins_by_casino, claim_history,
                last_24h_coins, last_7d_coins, last_30d_coins)
    
    try:
        analytics_data = retry_db_operation(get_analytics_data)
        return render_template('analytics.html',
                            total_coins=analytics_data[0],
                            success_rate=analytics_data[1],
                            coins_by_casino=analytics_data[2],
                            claim_history=analytics_data[3],
                            last_24h_coins=analytics_data[4],
                            last_7d_coins=analytics_data[5],
                            last_30d_coins=analytics_data[6])
    except OperationalError:
        flash('Unable to load analytics data. Please try again.', 'danger')
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    if os.environ.get('FLASK_ENV') == 'production':
        from load_balancer import LoadBalancer
        load_balancer = LoadBalancer(app)
        load_balancer.start()
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)