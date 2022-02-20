
from email.policy import default
from flask_wtf import FlaskForm
from sqlalchemy import true
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField, DateField,DateTimeField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_babel import _, lazy_gettext as _l
from fatwatch.models import Users, Customers
class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'),
                           validators=[DataRequired(), Length(min=2, max=20)])


    placeholder_comp=_l('Please select your company')
    companies = [placeholder_comp]+[ c for c, in Customers.query.with_entities(Customers.cust_name)]
    company = SelectField(_l('Company'),choices=companies, validators=[DataRequired(), Length(min=2, max=50)])

    roles = [(''),('role1'), ('role2')]
    role = SelectField(_l('Role'),
                           choices=roles,validators=[DataRequired(), Length(min=2, max=20)])

    languages = [(''),('en/EN'), ('nl/NL')]
    language = SelectField(_l('Language'),
                           choices=languages, validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    confirm_password = PasswordField(_l('Confirm Password'),
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Sign Up'))

    def validate_username(self, username):
        user=Users.query.filter_by(usr_name=username.data).first()
        if user:
            raise ValidationError(_l('That username is taken please choose another one.'))
            
    def validate_email(self, email):
        user=Users.query.filter_by(usr_email=email.data).first()
        if user:
            raise ValidationError(_l('There is another account registered with this email.'))

class LoginForm(FlaskForm):
    email = StringField(_l('Email'),
                        validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    token = StringField(_l('Token'), validators=[DataRequired(), Length(6, 6)])
    remember = BooleanField('Remember Me')
    submit = SubmitField(_l('Login'))        

class RequestResetForm(FlaskForm):
    email = StringField(_l('Email'),
                        validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))

    def validate_email(self, email):
        user = Users.query.filter_by(usr_email=email.data).first()
        if user is None:
            raise ValidationError(_l('There is no account with that email. You must register first.'))

class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    confirm_password = PasswordField(_l('Confirm Password'),
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Reset Password'))

class CustomersForm(FlaskForm):

    id = IntegerField('id')
    name = StringField(_l('Name'))
    address = StringField(_l('Address'))
    zip = StringField(_l('Zip'))
    city = StringField(_l('City'))
    phone = StringField(_l('Phone'))
    email = StringField(_l('E-mail'))

    active = BooleanField(_l('Active'),validators=None, false_values=None)

    timestamp = DateTimeField(_l('timestamp', format='%d-%m-%Y %H:%M:%S'))

    


