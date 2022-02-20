import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from psycopg2.extras import register_hstore
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_babel import Babel, lazy_gettext as _l
from flask_modals import Modal

load_dotenv()   



app = Flask(__name__)

db_user = os.environ.get('DB_USER')
db_psw = os.environ.get('DB_PSW')

conn = psycopg2.connect(dbname="fatwatch", user=db_user, password=db_psw, host="db-postgresql-ams3-fatwatch-do-user-10245331-0.b.db.ondigitalocean.com", port="25060")
cur = conn.cursor()
psycopg2.extras.register_hstore(conn)

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

#app.config['BABEL DEFAULT LOCALE']='en'
babel = Babel(app)
LANGUAGES = ['en', 'nl']
@babel.localeselector
def get_locale():
    return 'nl'
    #return request.accept_languages.best_match(app.config['LANGUAGES'])

modal = Modal(app)

from fatwatch import routes, models    # needs to be after the app


