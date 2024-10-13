from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mailman import Mail
from flask_apscheduler import APScheduler
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
mail = Mail(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Import and register blueprints
from main import main as main_blueprint
app.register_blueprint(main_blueprint)

# Import tasks and schedule them
from tasks import check_and_send_notifications
scheduler.add_job(id='check_notifications', func=check_and_send_notifications, trigger='interval', minutes=60)

if __name__ == '__main__':
    app.run()
