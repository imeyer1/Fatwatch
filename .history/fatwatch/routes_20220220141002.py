import sys,os, re
import base64
from io import BytesIO
from datetime import datetime
from xmlrpc.client import boolean
from dateutil.parser import *
import psycopg2
from psycopg2 import OperationalError, errorcodes, errors
from bs4 import BeautifulSoup
import urllib.request
from flask import render_template, url_for, flash, redirect, session,  abort, request, jsonify
from sqlalchemy import null

from fatwatch import app, db, mail, conn
from flask_login import login_user, current_user, logout_user, login_required
from fatwatch.forms import LoginForm, RegistrationForm, ResetPasswordForm, RequestResetForm, CustomersForm
from fatwatch.models import Users, Customers, Cameras, Endpicts, Extcalpoints, Extrinsics, Intrinsics, Pumps, Rawpicts, Stations, Settings,Visits
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from flask_babel import _, get_locale
from sqlalchemy.inspection import inspect
from flask_modals import render_template_modal
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


@app.route("/tables/<val>", methods=['GET', 'POST'])
@login_required
def tables(val):
    table = val
    match table:
        case "Customers":
            tableName = "customers"#Customers
            tbl_prefix = "cust_"
        case "Cameras":
            tableName = "cameras"#Cameras
            tbl_prefix = "cam_"
        case "Endpicts":
            tableName = Endpicts
            tbl_prefix = "ep_"
        case "Extcalpoints":
            tableName = Extcalpoints
            tbl_prefix = "ecp_"
        case "Extrinsics":
            tableName = Extrinsics
            tbl_prefix = "ec_"
        case "Intrinsics":
            tableName = Intrinsics
            tbl_prefix = "ic_"
        case "Pumps":
            tableName = Pumps
            tbl_prefix = "pmp_"
        case "Rawpicts":
            tableName = Rawpicts
            tbl_prefix = "rp_"
        case "Stations":
            tableName = Stations
            tbl_prefix = "pst_"
        case "Settings":
            tableName = Settings
            tbl_prefix = "set_"
        case "Users":
            tableName = Users
            tbl_prefix = "usr_"
        case "Visits":
            tableName = Visits
            tbl_prefix = "vis_"
        case _:
            return redirect(url_for('login')) 
    cur = conn.cursor()
    #column headers
    try:
        columns=tableName.__table__.columns
        query = "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name= '"+tableName+"';"
        cur.execute(query)
        headings= [row[0] for row in columns ]
        headings=[column.name for column in tableName.__table__.columns]
        headings = [item.replace(tbl_prefix,"") for item in headings] 
    except:
        conn.rollback()
    #columns
    if tableName == Users:
        try:
            cur.execute("SELECT * FROM " + tableName +" ORDER BY id")
            data = cur.fetchall()
        except:
            conn.rollback()
    else:
        try:
            data=tableName.query.all()
            # cur.execute("SELECT * FROM " + tableName +" ORDER BY "+tbl_prefix+"id")
            # data = cur.fetchall()
        except:
            conn.rollback()
    newData2=[]
    if len(newData) == 0:
        data=tuple()
        for h in headings:
            data = data + (" ",)
        newData2.append(data)
    else:
           
        #modifies None in ""
        newData = [tuple(s if s != 'Customers' else "" for s in tup) for tup in data]
        #format datetime
        
        for e in list(data):
            l=list(e)
            for x in l:
                if isinstance(x, datetime):
                    pos=e.index(x)
                    d = x.strptime(str(x),"%Y-%m-%d %H:%M:%S").strftime( "%d/%m/%Y %H:%M:%S")
                    l[pos]= d
                    newData2.append(l)
            
    return render_template('tables.html', title=tableName, prefix=tbl_prefix, headings= headings, data=newData2, username=current_user.usr_name)


#update
@app.route("/update",methods=["POST","GET"])
def update():
    
    cur = conn.cursor()
    if request.method == 'POST':
        # retreive table and column prefix from page
        table =request.form['title'].strip().lower()
        prefix = request.form['prefix'].strip()
        #retreive columns from database
        try:
            cur.execute("SELECT column_name FROM information_schema.columns  \
                WHERE table_schema = 'public' AND table_name='"+table+"';")
            headings= [row[0] for row in cur ] 
            columns = " = %s, ".join(headings[1:-1])
        except:
            conn.rollback()

        #retreive values from row
        data=request.form.getlist('arr[]')
        val= []

        for d in data[:-1]:
                #if data exists trimms the spaces
                
                d=d.strip().replace(" &nbsp;","").replace("&nbsp;","").replace("<br>","")
                if d == "":
                    string = None
                else:
                    string = d.strip()
                val.append(string)

        
        #set the ID value to last position
        val.append(val.pop(0))

        #update the database
        try:
            query= "UPDATE " + str(table)+ " SET " + columns + "= %s WHERE "+str(prefix)+"id = %s"
            cur.execute(query, val)
            conn.commit()       
        except Exception as error:
            print ("Oops! An exception has occured:", error)
            print ("Exception TYPE:", type(error))
            conn.rollback()
        # cur.close()
           
        return redirect(url_for('tables',val=str(table)))
            
 
#delete
@app.route('/delete', methods = ['GET', 'POST'])
def delete():
    
    table =request.form['title'].strip().lower()
    id = request.form['id'].strip()
    prefix = request.form['prefix'].strip()
    cur = conn.cursor()
    if request.method == 'POST':
        try:
            query= "DELETE FROM " + str(table)+ " WHERE "+str(prefix)+"id = "+ id
            cur.execute(query)
            conn.commit()
        except:
            conn.rollback()       
        cur.close()
 
    return redirect(url_for('tables'))
#add
@app.route("/add",methods=["POST","GET"])
def add():


        cur = conn.cursor()
        if request.method == 'POST':
            # retreive table and column prefix from page
            table =request.form['title'].strip().lower()
            #retreive columns from database
            try:
                cur.execute("SELECT column_name FROM information_schema.columns  \
                    WHERE table_schema = 'public' AND table_name='"+table+"';")
                headings= [row[0] for row in cur]
                columns = ", ".join(headings[1:-1])
            except:
                conn.rollback()
            #retreive values from row
            data=request.form.getlist('arr[]')
            data2= []
            format=""
            for d in data[1:-1]:
                    #if data exists trimms the spaces
                    if d:
                        string = d.strip()
                    else:
                        string = None
                    data2.append(string)
                    format +="%s, "
            f = "VALUES(" + format[:-2] + ")" 
        
            #set the ID value to last position
            
            
            #update the database
            # try:
            query= "INSERT INTO " + str(table)+ "(" + columns + ")"+f
            cur.execute(query, data2)
            conn.commit()   
            # except:
            #     conn.rollback()    
            cur.close()
            
            return redirect(url_for('tables',val=str(table)))
            # return render_template('customers.html')

#search
@app.route("/search",methods=["POST","GET"])
def search():
    query = table.query
    # retreive table and column prefix from page
    table =request.form['title'].strip().lower()
    prefix = request.form['prefix'].strip()
    search = request.form['searchText']
    query = table.query
    if search:
        query = query.filter(db.or_(
            # User.name.like(f'%{search}%'),
            # User.email.like(f'%{search}%')
        ))
    total_filtered = query.count()