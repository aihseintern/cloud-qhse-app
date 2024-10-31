from datetime import datetime, timedelta
from functools import wraps
import os
import random
import secrets
from flask import Blueprint, jsonify, render_template, flash, redirect, session, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
import pytz
from app import db
from app.models import User, Guest
from app.forms import ForgotForm, LoginForm, RegistrationForm, OTPForm, ResetPasswordForm
from flask_mail import Message
from colorama import Fore, Back, Style
from utils.message import OTPMessage

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.menu'))
    
    form = LoginForm()

    if form.validate_on_submit():        
        user = User.query.get(form.nik.data)
        
        if user is None:
            flash('Invalid NIK', 'danger')
            return redirect(url_for('auth.login'))

        if not user.approved:
            flash('Your account is not approved. Please contact the administrator.', 'danger')
            return redirect(url_for('auth.login'))

        if not user.penalty_time:
            # Generate and send OTP
            send_otp(user)
            flash('An OTP has been sent to your phone number.', 'info')
            return redirect(url_for('auth.otp_verify', user_id=user.id))  # Redirect to OTP verification page
        elif user.penalty_time and user.penalty_time < datetime.now():
            print(f'Penalty time expired for user {user.id}')
            user.penalty_time = None
            db.session.commit()
            session['failed_otp_attempts'] = 0
            flash('An OTP has been sent to your phone number.', 'info')
            send_otp(user)
            return redirect(url_for('auth.otp_verify', user_id=user.id))
        else:
            remaining_time = user.penalty_time - datetime.now()
            flash(f'Too many failed attempts. Please try again after {remaining_time.seconds} seconds.', 'danger')
    
    return render_template('login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()

    # Check if the form validates
    if form.validate_on_submit():
        # Check if NIK exists in the database and other fields are empty
        user = User.query.filter_by(id=form.nik.data).first()

        if user:
            # Ensure all other fields (name, email, etc.) are empty or None
            if any([user.name, user.email, user.phone_number]):
                flash("This NIK is already in use. Please contact support if this is an error.", "danger")
                return redirect(url_for('auth.register'))
            else:
                # NIK is valid and other fields are empty, proceed with registration
                if form.phone.data.startswith('0'):
                    form.phone.data = '62' + form.phone.data[1:]
                
                # Update user fields with the form data
                user.name = form.name.data
                user.email = form.email.data
                user.phone_number = form.phone.data
                user.role = form.role.data
                
                db.session.commit()
                flash('Registration successful. Please wait for approval.', 'success')
                return redirect(url_for('auth.login'))
        else:
            # NIK doesn't exist in the database
            flash('This NIK is not available. Please enter a valid NIK.', 'danger')
            return redirect(url_for('auth.register'))
    
    # If validation fails, check for specific error messages and flash them
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{error}", 'danger')

    return render_template('register.html', form=form)

@auth.route('/check_nik/<nik>', methods=['GET'])
def check_nik(nik):
    # Check if NIK exists in the database
    user = User.query.filter_by(id=nik).first()
    # Debugging print statements
    print(f"Checking NIK: {nik}")
    if user:
        print(f"User found: {user.id}")
    else:
        print("User is None")
    
    if user and all(field is None or field == '' for field in [user.name, user.email, user.phone_number, user.role]):
        # NIK exists and all other fields are empty or None
        return jsonify({'valid': True})
    
    # Either NIK does not exist or it is already in use
    return jsonify({'valid': False})

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('role', None) 
    session.clear()
    return redirect(url_for('auth.login'))

@auth.route('/otp_verify/<user_id>', methods=['GET', 'POST'])
def otp_verify(user_id):
    user = User.query.get(user_id)
    
    if not user:
        flash('Invalid user', 'danger')
        return redirect(url_for('auth.login'))
    
    # Initialize failed attempts in session
    if 'failed_otp_attempts' not in session:
        session['failed_otp_attempts'] = 0
        
    # Check if the user is currently in a penalty period
    if user.penalty_time and user.penalty_time > datetime.now():
        remaining_time = user.penalty_time - datetime.now()
        flash(f'Too many failed attempts. Please try again after {remaining_time.seconds} seconds.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = OTPForm()
    
    # Buat bypass otp (development only)
    # login_user(user)
    # if user.is_admin():
    #     return redirect(url_for('admin.menu'))
    # return redirect(url_for('main.index'))

    if form.validate_on_submit():
        if verify_otp(user, form.otp_code.data):
            session['failed_otp_attempts'] = 0
            user.penalty_time = None
            login_user(user)
            if user.is_admin():
                return redirect(url_for('admin.menu'))
            return redirect(url_for('main.index'))
        else:
            session['failed_otp_attempts'] += 1
            if session['failed_otp_attempts'] >= 3 and not user.penalty_time:
                # Set penalty time to 20 seconds from now
                user.penalty_time = datetime.now() + timedelta(seconds=20)
                db.session.commit()  # Save penalty time to the database
                flash('Too many failed attempts. Please try again after 20 seconds.', 'danger')
                return redirect(url_for('auth.login'))
            elif session['failed_otp_attempts'] >= 3 and user.penalty_time:
                remaining_time = user.penalty_time - datetime.now()
                flash(f'Too many failed attempts. Please try again after {remaining_time.seconds} seconds.', 'danger')
                return redirect(url_for('auth.login'))
            else:    
                flash('Invalid or expired OTP', 'danger')
                return redirect(url_for('auth.otp_verify', user_id=user.id))

    return render_template('otp_verify.html', form=form, user_id=user.id)

@auth.route('/forgot', methods=['GET', 'POST'])
def forgot():    
    form = ForgotForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=form.nik.data).first()
        if user:
            send_otp(user)
            censored_phone_number = user.phone_number[:3] + '****' + user.phone_number[-3:]
            flash(f'An OTP has been sent to your phone number {censored_phone_number}.', 'info')
            return redirect(url_for('auth.otp_verify', user_id=user.id))  # Redirect to OTP verification page
        else:
            flash('Email not found. Please register first.', 'danger')

def generate_otp():
    return str(secrets.randbelow(900000)+ 100000)

def send_otp(user):
    otp_code = generate_otp()
    print('OTP Code:', otp_code)
    user.otp_code = otp_code
    user.otp_expiration = datetime.utcnow() + timedelta(minutes=5)
    db.session.commit()

    # Send OTP via email
    message = f"Your OTP is {otp_code}. It will expire in 5 minutes."
    msg = OTPMessage(phone_number=user.phone_number, message=message)    
    # msg.send()

def verify_otp(user, otp_code):
    if user.otp_code == otp_code and user.otp_expiration > datetime.utcnow():
        # Reset OTP and expiration fields
        user.otp_code = None
        user.otp_expiration = None
        db.session.commit()  # Save changes to the database
        return True
    return False

def otp_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        otp_expiry = session.get('otp_expiry')
        if not otp_expiry or datetime.now(pytz.utc) > otp_expiry:
            return redirect(url_for('auth.guidebot_login'))
        return func(*args, **kwargs)
    return wrapper

@auth.route("/guidebot_login", methods=['GET', 'POST'])
def guidebot_login():
    # if current_user.is_authenticated:
    #     print("User authenticated")
    #     return redirect(url_for('guide_bot.chat'))
    
    form = OTPForm()
    if form.validate_on_submit():
        email = form.email.data
        password_or_otp = form.otp.data  # OTP is used as a password in the form
        
        action = request.form.get('action')

        # Determine which action to take based on the form button pressed
        if action == 'login':
            # Handle login action
            # Check if the user exists in the database
            if 'otp' not in session or session.get('otp_email') != email:
                flash('Invalid OTP or email.', 'danger')
                return redirect(url_for('auth.guidebot_login'))

            if session.get('otp') != password_or_otp:
                flash('Invalid OTP. Please try again.', 'danger')
                return redirect(url_for('auth.guidebot_login'))
            
            print("date time now:", datetime.now(pytz.utc))
            print('otp expiry', session.get('otp_expiry'))
            
            # Get the current time in UTC
            if datetime.now(pytz.utc) > session.get('otp_expiry'):
                flash('OTP expired. Please request a new one.', 'danger')
                return redirect(url_for('auth.guidebot_login'))
            
            print(Fore.BLUE)
            print(f"Session OTP Email: {session.get('otp_email')}")
            print(f"Session OTP: {session.get('otp')}")
            print(f"Session OTP Expiry: {session.get('otp_expiry')}")
            print(Style.RESET_ALL)

            print("LOGIN")
            # Redirect to the chat page after successful login
            return redirect(url_for('guide_bot.chat'))
        
        elif action == 'request_otp':
            # Handle OTP request action
            if not email:
                flash('Email is required to request an OTP.', 'danger')
                return redirect(url_for('auth.guidebot_login'))

            # Generate OTP and set expiry time
            otp = generate_otp()
            expiry_time = datetime.now() + timedelta(minutes=OTP_EXPIRY_TIME)

            # Store OTP and expiry time in session
            session['otp'] = otp
            session['otp_expiry'] = expiry_time
            session['otp_email'] = email
            print(Fore.BLUE)
            print(f"Generated OTP: {otp}, Expiry: {expiry_time}")
            print(f"Session OTP Email: {session.get('otp_email')}")
            print(f"Session OTP: {session.get('otp')}")
            print(f"Session OTP Expiry: {session.get('otp_expiry')}")
            print(Style.RESET_ALL)

            # Send OTP via email
            from app import mail
            msg = Message(subject='Your OTP for Guidebot Login', sender=os.getenv('MAIL_USERNAME'), recipients=[email])
            msg.body = f"Your OTP is {otp}. It will expire in {OTP_EXPIRY_TIME} minutes."

            try:
                mail.send(msg)
                flash('An OTP has been sent to your email. Please check your inbox.', 'info')
            except Exception as e:
                print(f"Error sending email: {e}")
                flash('Failed to send OTP to email. Please try again later.', 'danger')
            print("REQ OTP")
            return redirect(url_for('auth.guidebot_login'))
        
    return render_template('guide_bot/guidebot_login.html', form=form)

OTP_EXPIRY_TIME = 3  # minutes

@auth.route("/guidebot_logout", methods=['GET', 'POST'])
def guidebot_logout():
    # Clear OTP data from session after successful login
    session.pop('otp', None)
    session.pop('otp_expiry', None)
    session.pop('otp_email', None)
    return redirect(url_for('auth.guidebot_login'))
    
@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotForm()
    if form.validate_on_submit():
        # user = User.query.filter_by(email=form.email.data).first()
        session['otp_email'] = form.email.data
        if form.email.data:
            send_password_reset_email()
        else:
            flash('Email not found. Please register first.', 'danger')
        return redirect(url_for('auth.reset_password'))
    return render_template('forgot_password.html', form=form)

def send_password_reset_email():
    otp = generate_otp()
    expiry_time = datetime.now() + timedelta(minutes=OTP_EXPIRY_TIME)
    
    # Store OTP and expiry time in session
    session['otp'] = otp
    session['otp_expiry'] = expiry_time
    
    # Send OTP via email
    from app import mail
    msg = Message(subject='Your OTP for Forgot Password', sender=os.getenv('MAIL_USERNAME'), recipients=[session.get('otp_email')])
    msg.body = f"Your OTP is {otp}. It will expire in {OTP_EXPIRY_TIME} minutes."

    try:
        mail.send(msg)
        flash('An OTP has been sent to your email. Please check your inbox.', 'info')
    except Exception as e:
        print(f"Error sending email: {e}")
        flash('Failed to send OTP to email. Please try again later.', 'danger')
    print("REQ OTP")
     
@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if form.otp.data == session.get('otp'):
            if form.password.data == form.password2.data:
                user = User.query.filter_by(email=session.get('otp_email')).first()
                if user:
                    user.set_password(form.password.data)
                    # user.password_hash = form.password.data
                    db.session.commit()
                    flash('Password reset successful. You can now login.', 'success')
                    return redirect(url_for('auth.login'))
                else:
                    flash('User not found. Please register first.', 'danger')
            else:
                flash('Passwords do not match. Please try again.', 'danger')
        else:   
            flash('Invalid OTP. Please try again.', 'danger')
    return render_template('reset_password.html', form=form)