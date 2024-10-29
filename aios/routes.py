# aios/routes.py
from datetime import datetime, timedelta
from flask import Blueprint, render_template, flash, redirect, request, session, url_for, Response, stream_with_context, abort, jsonify
from flask_login import current_user, login_user, logout_user, login_required
import pytz

from app.auth import otp_required

aios = Blueprint('aios', __name__)

@aios.route('/aios')
# @otp_required
def index():
    return render_template('aios/base.html')

OTP_EXPIRY_TIME = 1

@aios.before_request
def update_last_request_time():
    # Check if the request path contains '/aios'
    if '/aios' in request.base_url:
        # Get the current time
        now = datetime.now(pytz.utc)

        # Check if the session contains the OTP and expiry time
        if 'otp' in session and 'otp_expiry' in session:
            expiry_time = session['otp_expiry']
            
            if now > expiry_time:
                # If the current time is past the expiry time, clear the OTP session and redirect
                session.pop('otp', None)  # Remove OTP session
                session.pop('otp_expiry', None)  # Remove expiry time
                print("session timeout")
                return redirect(url_for('auth.guidebot_login'))  # Redirect to login page
        
        # Update the OTP expiry time to current time plus 5 minutes
        session['otp_expiry'] = now + timedelta(minutes=OTP_EXPIRY_TIME)
        print(f"otp expiry got updated: {session['otp_expiry']}")
        
    else:
        print('url doesnt contain /aios:', request.base_url)