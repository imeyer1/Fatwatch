from datetime import datetime
import os
import base64
import onetimepass
from fatwatch import db, loginManager, app
from flask_login import UserMixin # class contains isAuthenticate, isActive, isAnonimous, getID
from werkzeug.security import  check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer




@loginManager.user_loader
def load_user(id):
     return Users.query.get(int(id))

class Customers(db.Model):
    cust_id = db.Column(db.Integer, primary_key=True)
    cust_name = db.Column(db.String, unique=True, nullable=False) 
    cust_address = db.Column(db.String, nullable=False)
    cust_zip = db.Column(db.String(10), nullable=False)
    cust_city = db.Column(db.String(), nullable=False)
    cust_email = db.Column(db.String(), nullable=False)
    cust_phone = db.Column(db.String())
    cust_active = db.Column(db.Boolean, default=1)
    cust_timestamp = db.Column(db.DateTime,default = datetime.now)
    
    cust_to_usr = usr_to_pst = db.relationship('Users', foreign_keys='Users.usr_cust_id',lazy = 'select', backref = db.backref('customers', lazy = 'joined'))

    
    def __repr__(self):
        return  self.cust_name, self.cust_address, self.cust_zip, self.cust_city, self.cust_phone, self.cust_email, self.cust_active, self.cust_timestamp
    
    def to_dict(self):
        return {
            'id': self.cust_id,
            'name': self.cust_name,
            'address': self.cust_address,
            'zip': self.cust_zip,
            'city': self.cust_city,
            'email': self.cust_email,
            'phone': self.cust_phone,
            'active': self.cust_active,
            'timestamp': self.cust_timestamp
        }

    def is_active(self):
        if self.active:
            return "true"
        else:
            return "false"


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    usr_timestamp = db.Column(db.DateTime, default = datetime.now)
    usr_name = db.Column(db.String(50), unique=True, nullable=False)
    usr_email = db.Column(db.String(120), unique=True, nullable=False)
    usr_psw = db.Column(db.String(128), nullable=False)
    usr_company = db.Column(db.String(60))
    usr_role = db.Column(db.String(60))
    usr_active = db.Column(db.Boolean, default=1)
    usr_otp_secret = db.Column(db.String(16))
    usr_lang = db.Column(db.String(6))
    usr_ip = db.Column(db.String)
    
    usr_cust_id = db.Column(db.Integer, db.ForeignKey('customers.cust_id'))
    usr_to_pst = db.relationship('Stations', foreign_keys='Stations.pst_usr_id',lazy = 'select', backref = db.backref('users', lazy = 'joined'))

    def __init__(self, **kwargs):
        super(Users, self).__init__(**kwargs)
        if self.usr_otp_secret is None:
            # generate a random secret
            self.usr_otp_secret = base64.b32encode(os.urandom(10)).decode('utf-8')

    def verify_password(self, password):
        return check_password_hash(self.usr_psw, password)

    def get_totp_uri(self):
        return 'otpauth://totp/{0}?secret={1}&issuer=FATWatch' \
            .format(self.usr_name, self.usr_otp_secret)

    def verify_totp(self, token):
        return onetimepass.valid_totp(token, self.usr_otp_secret)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')
        
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return Users.query.get(user_id)

    def __repr__(self):
        return f"Users( '{self.id}','{self.usr_name}','{self.usr_email}','{self.usr_company}',{self.usr_role}','{self.usr_active}','{self.usr_lang}', '{self.usr_ip}')"

class Stations(db.Model):
    pst_id = db.Column(db.Integer, primary_key=True)
    pst_timestamp = db.Column(db.DateTime, default = datetime.now)
    pst_name = db.Column(db.String(), unique=True, nullable=False)
    pst_address = db.Column(db.String(), nullable=False)
    pst_cron = db.Column(db.Integer(), nullable=False)

    pst_usr_id = db.Column(db.Integer, db.ForeignKey('users.id'),nullable=False)
    
    pst_to_pmp = db.relationship('Pumps', foreign_keys='Pumps.pmp_pst_id', lazy = 'select', backref = db.backref('stations', lazy = 'joined'))
    pst_to_vis = db.relationship('Visits', foreign_keys='Visits.vis_pst_id', lazy = 'select', backref = db.backref('stations', lazy = 'joined'))
    pst_to_cam = db.relationship('Cameras', foreign_keys='Cameras.cam_pst_id', lazy = 'select', backref = db.backref('stations', lazy = 'joined'))



class Pumps(db.Model):
    pmp_id = db.Column(db.Integer, primary_key=True)
    pmp_timestamp = db.Column(db.DateTime, default = datetime.now)
    pmp_name = db.Column(db.String(), unique=True, nullable=False)
    pmp_type = db.Column(db.String(), nullable=False)

    pmp_pst_id = db.Column(db.Integer, db.ForeignKey('stations.pst_id'),nullable=False)



class Visits(db.Model):
    vis_id = db.Column(db.Integer, primary_key=True)
    vis_timestamp = db.Column(db.DateTime, default = datetime.now)
    via_engineer = db.Column(db.String(), unique=True, nullable=False)
    vis_note = db.Column(db.String(), nullable=True)
    vis_pict = db.Column(db.String(), nullable=True)

    vis_pst_id = db.Column(db.Integer, db.ForeignKey('stations.pst_id'),nullable=False)



class Cameras(db.Model):
    cam_id = db.Column(db.Integer, primary_key=True)
    cam_timestamp = db.Column(db.DateTime, default = datetime.now)
    cam_sn = db.Column(db.String(), unique=True, nullable=False)
    cam_start = db.Column(db.DateTime)
    cam_stop = db.Column(db.DateTime)
    cam_active = db.Column(db.Boolean)
    cam_con = db.Column(db.Boolean)
    cam_type = db.Column(db.String(), nullable=False)

    cam_pst_id = db.Column(db.Integer, db.ForeignKey('stations.pst_id'),nullable=False)

    cam_to_ic = db.relationship('Intrinsics', foreign_keys='Intrinsics.ic_cam_id',lazy = 'select', backref = db.backref('cameras', lazy = 'joined'))
    cam_to_ec = db.relationship('Extrinsics', foreign_keys='Extrinsics.ec_cam_id', lazy = 'select', backref = db.backref('cameras', lazy = 'joined'))
    cam_to_rp = db.relationship('Rawpicts', foreign_keys='Rawpicts.rp_cam_id', lazy = 'select', backref = db.backref('cameras', lazy = 'joined'))
    cam_to_ep = db.relationship('Endpicts', foreign_keys='Endpicts.ep_cam_id', lazy = 'select', backref = db.backref('cameras', lazy = 'joined'))




class Intrinsics(db.Model):
    ic_id = db.Column(db.Integer, primary_key=True)
    ic_timestamp = db.Column(db.DateTime, default = datetime.now)
    ic_check = db.Column(db.Numeric)
    ic_fx = db.Column(db.Numeric)
    ic_fy = db.Column(db.Numeric)
    ic_s = db.Column(db.Numeric)
    ic_cx = db.Column(db.Numeric)
    ic_cy = db.Column(db.Numeric)
    ic_repe = db.Column(db.Numeric)
    ic_fov = db.Column(db.Numeric)
    ic_k1 = db.Column(db.Numeric)
    ic_k2 = db.Column(db.Numeric)
    ic_k3 = db.Column(db.Numeric)
    ic_p1 = db.Column(db.Numeric)
    ic_p2 = db.Column(db.Numeric)
    ic_lab = db.Column(db.Numeric)
    ic_a0 = db.Column(db.Numeric)
    ic_a1 = db.Column(db.Numeric)
    ic_a2 = db.Column(db.Numeric)
    ic_a3 = db.Column(db.Numeric)
    ic_a4 =  db.Column(db.Numeric)
    ic_pict1 = db.Column(db.String())
    ic_pict2 = db.Column(db.String())
    ic_pict3 = db.Column(db.String())
    ic_pict4 = db.Column(db.String())
    ic_pict5 = db.Column(db.String())
    ic_pict6 = db.Column(db.String())
    ic_pict7 = db.Column(db.String())
    ic_pict8 = db.Column(db.String())
    ic_pict9 = db.Column(db.String())
    ic_pict10 = db.Column(db.String())
    ic_pict11 = db.Column(db.String())
    ic_pict12 = db.Column(db.String())
    ic_pict13 = db.Column(db.String())
    ic_pict14 = db.Column(db.String())
    ic_pict15 = db.Column(db.String())

    
    ic_cam_id = db.Column(db.Integer, db.ForeignKey('cameras.cam_id'),nullable=False)
    



class Extrinsics(db.Model):
    ec_id = db.Column(db.Integer, primary_key=True)
    ec_timestamp = db.Column(db.DateTime, default = datetime.now)
    ec_pict = db.Column(db.String())
    ec_t1 = db.Column(db.Numeric)
    ec_t2 = db.Column(db.Numeric)
    ec_t3 = db.Column(db.Numeric)
    ec_r11 = db.Column(db.Numeric)
    ec_r12 = db.Column(db.Numeric)
    ec_r13 = db.Column(db.Numeric)
    ec_r21 = db.Column(db.Numeric)
    ec_r22 = db.Column(db.Numeric)
    ec_r23 = db.Column(db.Numeric)
    ec_r31 = db.Column(db.Numeric)
    ec_r32 = db.Column(db.Numeric)
    ec_r33 = db.Column(db.Numeric)
    
    ec_cam_id = db.Column(db.Integer, db.ForeignKey('cameras.cam_id'),nullable=False)
    ec_to_ecp = db.relationship('Extcalpoints', foreign_keys='Extcalpoints.ecp_ec_id', lazy = 'select', backref = db.backref('extrinsics', lazy = 'joined'))
    



class Extcalpoints(db.Model):
    ecp_id = db.Column(db.Integer, primary_key=True)
    ecp_timestamp = db.Column(db.DateTime, default = datetime.now)
    ecp_p1 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p2 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p3 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p4 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p5 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p6 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p7 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p8 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p9 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p10 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p11 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p12 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p13 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p14 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p15 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p16 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p17 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p18 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p19 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p20 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p21 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p22 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p23 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p24 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p25 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p26 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p27 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p28 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p29 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))
    ecp_p30 = db.Column(db.ARRAY(db.Numeric, dimensions = 3))

    
    
    ecp_ec_id = db.Column(db.Integer, db.ForeignKey('extrinsics.ec_id'),nullable=False)
    

class Rawpicts(db.Model):
    rp_id = db.Column(db.Integer, primary_key=True)
    rp_timestamp = db.Column(db.DateTime, default = datetime.now)
    rp_name = db.Column(db.String())
    rp_path = db.Column(db.String())
    rp_range = db.Column(db.String())

    
    rp_cam_id = db.Column(db.Integer, db.ForeignKey('cameras.cam_id'),nullable=False)
    rp_ep_id = db.Column(db.Integer, db.ForeignKey('endpicts.ep_id'),nullable=False)



class Endpicts(db.Model):
    ep_id = db.Column(db.Integer, primary_key=True)
    ep_timestamp = db.Column(db.DateTime, default = datetime.now)
    ep_name = db.Column(db.String())
    ep_path = db.Column(db.String())
    ep_range = db.Column(db.String())
    ep_fat = db.Column(db.Numeric)
    ep_water = db.Column(db.Numeric)
    ep_construct = db.Column(db.Numeric)


    
    ep_cam_id = db.Column(db.Integer, db.ForeignKey('cameras.cam_id'),nullable=False)
    ep_to_rp = db.relationship('Rawpicts', foreign_keys='Rawpicts.rp_ep_id', lazy = 'select', backref = db.backref('endpicts', lazy = 'joined'))



class Settings(db.Model):
    set_id = db.Column(db.Integer, primary_key=True)
    set_timestamp = db.Column(db.DateTime, default = datetime.now)
    set_rawpath = db.Column(db.String())
    set_endpath = db.Column(db.String())
    set_icpath = db.Column(db.String())
    set_visitpath = db.Column(db.String())



    
    