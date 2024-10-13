from app import mail
from flask_mail import Message
from flask import url_for

def send_notification_email(user, casino):
    msg = Message('Free Coins Available!',
                  recipients=[user.email])
    msg.body = f"Hello {user.username},\n\nYour free coins are now available for collection in {casino.name}!\n\nVisit your dashboard to collect them: {url_for('main.dashboard', _external=True)}\n\nRemember to play responsibly!"
    mail.send(msg)
