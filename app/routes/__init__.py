import os
from app.routes.cctv import cctv_bp
from app.routes.contact import contact_bp
from app.routes.detector import detector_bp
from app.routes.document import document_bp
from app.routes.message import message_bp
from app.routes.notification import notification_bp
from app.routes.report import report_bp
from app.routes.weight import weight_bp
from app.routes.admin import admin_bp
from app.routes.dg_classifier import dg_classifier_bp
from guide_bot.routes import guide_bot
from datetime import datetime, timedelta
from collections import Counter
from flask import (
    Blueprint,
    render_template,
    flash,
    redirect,
    request,
    send_from_directory,
    session,
    url_for,
    Response,
    stream_with_context,
    abort,
    jsonify,
)
from app.extensions import db
from app.models import (
    CCTV,
    Contact,
    DetectedObject,
    Detector,
    DetectorType,
    MessageTemplate,
    NotificationRule,
    Permission,
    User,
    UserPermission,
    Weight,
    suMenu,
)
from flask_login import current_user, login_user, logout_user, login_required
import logging
from utils.auth import get_allowed_permission_ids

app_routes = [
    cctv_bp,
    contact_bp,
    detector_bp,
    document_bp,
    message_bp,
    notification_bp,
    report_bp,
    weight_bp,
    admin_bp,
    guide_bot,
    dg_classifier_bp
]

main = Blueprint("main", __name__)

@main.route("/", methods=["GET"])
@login_required
def index():    
    # Get the permission IDs for the current user
    allowed_permission_ids = get_allowed_permission_ids()    
    
    # Query the suMenu model for menus associated with those permission IDs
    menus = suMenu.query.filter(suMenu.permission_id.in_(allowed_permission_ids)).all()
    
    # Render the index template and pass the menu data
    return render_template("index.html", menus=menus)

@main.route('/set_session', methods=['POST'])
def set_session():
    permission_id = request.form.get('id')    
    if permission_id:
        permission = Permission.query.get(permission_id)
        session['permission_name'] = permission.name
        session['permission_id'] = permission_id
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'error', 'message': 'No ID provided'}), 400

@main.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        from app import UPLOAD_FOLDER
        return send_from_directory(UPLOAD_FOLDER, filename)
    except FileNotFoundError:
        abort(404)

@main.app_context_processor
def inject_session_permission():
    return dict(session_permission=session.get('permission_id', ''), permission_name=session.get('permission_name', ''))
