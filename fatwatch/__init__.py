import os
from dotenv import load_dotenv
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_babel import Babel
load_dotenv()   



app = Flask(__name__)

db_user = os.environ.get('DB_USER')
db_psw = os.environ.get('DB_PSW')


app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URL')

db=SQLAlchemy(app)
migrate=Migrate(app, db)

loginManager = LoginManager(app)
loginManager.login_view = 'login'

app.config['MAIL_SERVER'] = 'mail.xel.nl'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)

babel = Babel(app)
LANGUAGES = ['en', 'nl']
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

from fatwatch import routes, models    # needs to be after the app


