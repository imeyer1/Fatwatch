from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail




app = Flask(__name__)

app.config['SECRET_KEY'] = "cced3a87ab112f0bd9814216f6814ebf"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://doadmin:4CWzQsqGZs9B9E6f@db-postgresql-ams3-fatwatch-do-user-10245331-0.b.db.ondigitalocean.com:25060/fatwatch"

db=SQLAlchemy(app)
migrate=Migrate(app, db)

loginManager = LoginManager(app)
loginManager.login_view = 'login'

app.config['MAIL_SERVER'] = 'mail.xel.nl'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = "noreply@skillsinmotion.nl"
app.config['MAIL_PASSWORD'] = "m;1SkG[x=xC*/T"
mail = Mail(app)

from fatwatch import routes, models    # needs to be after the app


