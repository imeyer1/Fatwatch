
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, validators, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from fatwatch.models import Users, Customers
class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])


   
    companies = ['Please select your company']+[ c for c, in Customers.query.with_entities(Customers.cust_name)]
    company = SelectField('Company',choices=companies, validators=[DataRequired(), Length(min=2, max=50)])

    roles = [(''),('role1'), ('role2')]
    role = SelectField('Role',
                           choices=roles,validators=[DataRequired(), Length(min=2, max=20)])

    languages = [(''),('en/EN'), ('nl/NL')]
    language = SelectField('Language',
                           choices=languages, validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user=Users.query.filter_by(usr_name=username.data).first()
        if user:
            raise ValidationError('That username is taken please choose another one.')
            
    def validate_email(self, email):
        user=Users.query.filter_by(usr_email=email.data).first()
        if user:
            raise ValidationError('There is another account registered with this email.')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    token = StringField('Token', validators=[DataRequired(), Length(6, 6)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')        

class CustomersForm(FlaskForm):
    customerName = StringField('Name')
    customerAddress = StringField('Address')
    customerZip = StringField('Zip')
    customerCity = StringField('City')
    customerPhone = StringField('Phone')
    customerEmail = StringField('E-mail')


