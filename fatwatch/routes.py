import os
import base64
from io import BytesIO
from flask import render_template, url_for, flash, redirect, session,  abort
from fatwatch import app, db
from flask_login import login_user, current_user, logout_user, login_required
from fatwatch.forms import LoginForm, RegistrationForm, CustomersForm
from fatwatch.models import Users, Customers
from werkzeug.security import generate_password_hash, check_password_hash
import onetimepass
import pyqrcode


@app.route("/", methods=['GET', 'POST'])
# @app.route("/home")
# def home():
#     return render_template('main.html')


@app.route("/register", methods=['GET', 'POST'])

def register():
    if current_user.is_authenticated:
        # if user is logged in we get out of here
        return redirect(url_for('main'))
    form = RegistrationForm()

    
    if form.validate_on_submit():
        psw = generate_password_hash(form.password.data)

        # add new user to the database
        user = Users(usr_name=form.username.data, usr_company=form.company.data, usr_role=form.role.data, usr_lang=form.language.data, usr_email=form.email.data, usr_psw=psw)
        db.session.add(user)
        db.session.commit()
       
        # redirect to the two-factor auth page, passing username in session
        session['username'] = user.usr_name
        return redirect(url_for('two_factor_setup'))
    return render_template('register.html', form=form)
        
@app.route('/twofactor')
def two_factor_setup():
    if 'username' not in session:
        return redirect(url_for('index'))
    user = Users.query.filter_by(usr_name=session['username']).first()
    if user is None:
        return redirect(url_for('index'))
    # since this page contains the sensitive qrcode, make sure the browser
    # does not cache it
    return render_template('two-factor-setup.html'), 200, {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'}

@app.route('/qrcode', methods=['GET', 'POST'])
def qrcode():
    if 'username' not in session:
        abort(404)
    user = Users.query.filter_by(usr_name=session['username']).first()
    if user is None:
        abort(404)

    # for added security, remove username from session
    del session['username']

    # render qrcode for FreeTOTP
    url = pyqrcode.create(user.get_totp_uri())
    stream = BytesIO()
    url.svg(stream, scale=3)
    return stream.getvalue(), 200, {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'}

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # if user is logged in we get out of here
        return redirect(url_for('main'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(usr_email=form.email.data).first()
        if user is None or not user.verify_password(form.password.data) or \
                not user.verify_totp(form.token.data):
            flash('Invalid username, password or token.')
            return redirect(url_for('login'))

        # log user in
        login_user(user)
        flash('You are now logged in!')
        return redirect(url_for('customer.html'))
    return render_template('login.html', title='Login', form=form)

@app.route("/customers", methods=['GET', 'POST'])
@login_required
def customer():
    form = CustomersForm()
    customers = Customers.query.all()
    customer_detail = Customers.query.first()
    return render_template('customers.html', title='Contacts', username=current_user.usr_name, form=form, customer=customers, customer_detail=customer_detail)
