from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user, current_user
from urllib.parse import urlparse
from app import db, login_manager, mail
from models import User, Casino
from forms import LoginForm, RegistrationForm, AddCasinoForm
from flask_mail import Message
from datetime import datetime, timedelta

main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@main.route('/dashboard')
@login_required
def dashboard():
    casinos = current_user.casinos.all()
    return render_template('dashboard.html', casinos=casinos)

@main.route('/add_casino', methods=['GET', 'POST'])
@login_required
def add_casino():
    form = AddCasinoForm()
    if form.validate_on_submit():
        casino = Casino(name=form.name.data, collection_interval=form.collection_interval.data, user=current_user)
        casino.update_next_collection()
        db.session.add(casino)
        db.session.commit()
        flash('Casino added successfully!')
        return redirect(url_for('main.dashboard'))
    return render_template('add_casino.html', form=form)

@main.route('/collect/<int:casino_id>')
@login_required
def collect(casino_id):
    casino = Casino.query.get_or_404(casino_id)
    if casino.user != current_user:
        flash('You do not have permission to collect from this casino.')
        return redirect(url_for('main.dashboard'))
    casino.last_collection = datetime.utcnow()
    casino.update_next_collection()
    db.session.commit()
    flash(f'Collected coins from {casino.name}!')
    return redirect(url_for('main.dashboard'))

@main.route('/responsible_gaming')
def responsible_gaming():
    return render_template('responsible_gaming.html')

def send_notification_email(user, casino):
    msg = Message('Free Coins Available!',
                  recipients=[user.email])
    msg.body = f"Hello {user.username},\n\nYour free coins are now available for collection in {casino.name}!\n\nVisit your dashboard to collect them: {url_for('main.dashboard', _external=True)}\n\nRemember to play responsibly!"
    mail.send(msg)

# Schedule this function to run periodically (e.g., every hour)
def check_and_send_notifications():
    now = datetime.utcnow()
    casinos_due = Casino.query.filter(Casino.next_collection <= now).all()
    for casino in casinos_due:
        send_notification_email(casino.user, casino)
