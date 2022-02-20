import os
import base64
from io import BytesIO
import psycopg2
from flask import render_template, url_for, flash, redirect, session,  abort, request
from fatwatch import app, db, mail, conn
from flask_login import login_user, current_user, logout_user, login_required
from fatwatch.forms import LoginForm, RegistrationForm, ResetPasswordForm, RequestResetForm, CustomersForm
from fatwatch.models import Users, Customers
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from flask_babel import _, get_locale
from sqlalchemy.inspection import inspect
import pyqrcode


@app.route("/", methods=['GET', 'POST'])
# @app.route("/home")
# def home():
#     return render_template('main.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    # if current_user.is_authenticated:
    #     # if user is logged in we get out of here
    #     return redirect(url_for('main'))
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

@app.route("/login", methods=['GET', 'POST'])
def login():
    # if current_user.is_authenticated:
    #     # if user is logged in we get out of here
    #     return redirect(url_for('login'))
    form = LoginForm()
    if current_user.is_authenticated == False:
        # if user has IP bypass login
        print(request.remote_addr)
        user = Users.query.filter_by(usr_ip=request.remote_addr).first()
        login_user(user, remember=form.remember.data)
        return  redirect(url_for('login'))            
        
    if form.validate_on_submit():
        print(Users.usr_ip)
        user = Users.query.filter_by(usr_email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data) or \
                    not user.verify_totp(form.token.data):
                flash('Invalid username, password or token.')
                return redirect(url_for('login'))

            # log user in
        login_user(user)
        flash('You are now logged in!')
        return redirect(url_for('customers'))
    return render_template('login.html', title='Login', form=form)



        
@app.route('/twofactor')
def two_factor_setup():
    if 'username' not in session:
        return redirect(url_for('index'))
    user = Users.query.filter_by(usr_name=session['username']).first()
    if user is None:
        return redirect(url_for('index'))
    # since this page contains the sensitive qrcode, make sure the browser
    # does not cache it
    return render_template('two_factor_setup.html'), 200, {
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


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@skillsinmotion.nl',
                  recipients=[user.usr_email])
    msg.body = _('If you did not make this request then simply ignore this email and no changes will be made.\
    To reset your password, visit the following link. This link is valid for 30 minutes:')
    {url_for('reset_token', token=token, _external=True)}

    mail.send(msg)

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    # if current_user.is_authenticated:
    #     return redirect(url_for('customers'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(usr_email=form.email.data).first()
        send_reset_email(user)
        flash (_('An email has been sent with instructions to reset your password.', 'info'))
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    # if current_user.is_authenticated:
    #     return redirect(url_for('customers'))
    user = Users.verify_reset_token(token)
    if user is None:
        flash(_('That is an invalid or expired token', 'warning'))
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user.password = hashed_password
        db.session.commit()
        flash(_('Your password has been updated! You are now able to log in', 'success'))
        return redirect(url_for('login'))
    return render_template('reset_token.html', title=_('Reset Password'), form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))
    
#This is the route where we are going to
#query on all our customers data
@app.route("/customers", methods=['GET', 'POST'])
@login_required
def customers():
    form = CustomersForm()
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns  \
            WHERE table_schema = 'public' AND table_name='customers';")
    headings=column_names = [row[0] for row in cur]
    cur.execute("SELECT * FROM customers;")
    data = cur.fetchall()
    newData = [tuple(s if s != None else " " for s in tup) for tup in data]
    newData2 = [tuple(s if s != "true" else "true" for s in tup) for tup in newData]


    
    return render_template('customers.html', title='Contacts', headings= headings, data=newData2, username=current_user.usr_name, form=form)

#insert
@app.route('/insert', methods = ['POST'])
def insert():
 
    if request.method == 'POST':
 
        name = request.form['name']
        address = request.form['address']
        zip = request.form['zip']
        city = request.form['city']
        email = request.form['email']
        phone = request.form['phone']
        active = request.form['active']
 
        my_data = Customers(name,address, zip, city, email, phone).replace("None","")
        db.session.add(my_data)
        db.session.commit()
 
        flash("Customer Inserted Successfully")
 
        return redirect(url_for('customers'))
 
 #update
@app.route('/update', methods = ['GET', 'POST'])
def update():
    
    if request.method == 'POST':
        my_data = Customers.query.get(request.form.get('id'))
        my_data.id =  request.form['id']
        my_data.name = request.form['name']
        my_data.address = request.form['address']
        my_data.zip = request.form['zip']
        my_data.city = request.form['city']
        my_data.email = request.form['email']
        my_data.phone = request.form['phone']
        my_data.active = request.form['active']
       
 
        db.session.commit()
        flash("Employee Updated Successfully")
 
        return redirect(url_for('customers'))
 
 
 
 
#delete
@app.route('/delete/<id>/', methods = ['GET', 'POST'])
def delete(id):
    my_data = Customers.query.get(id)
    db.session.delete(my_data)
    db.session.commit()
    flash("Employee Deleted Successfully")
 
    return redirect(url_for('customers'))
 
 