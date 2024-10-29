import logging
from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, session, Response, jsonify
from flask_login import login_required
import requests
from app.models import MessageTemplate, NotificationRule
from app import db
from app.forms import MessageTemplateForm, NotificationRuleForm
from utils.auth import get_allowed_permission_ids
from flasgger import swag_from

logging.basicConfig(level=logging.DEBUG)

notification_bp = Blueprint('notification', __name__, url_prefix='/notification')

# NOTIFICATION
@notification_bp.route('/', methods=['GET'])
@notification_bp.route('/<int:id>', methods=['GET'])
@login_required
def view(id=None):
    if id:
        notification = NotificationRule.query.get_or_404(id)
        notification = {
            'id': notification.id,
            'name': notification.name,
            'description': notification.description,
            'permission_id': notification.permission_id
        }
        return jsonify(notification), 200
    else:
        notifications = NotificationRule.query.filter(NotificationRule.permission_id == session.get('permission_id')).all()
        messages = []
        for message in MessageTemplate.query.filter(MessageTemplate.permission_id == session.get('permission_id')).all():
            messages.append({
                'id': message.id,
                'name': message.name,
                'template': message.template,
                'permission_id': message.permission_id
            })
        logging.debug(f"Messages: {messages}")
        return render_template('manage_notification_rules.html', messages=messages, rules=notifications, rule_form=NotificationRuleForm(), message_form=MessageTemplateForm())
    
@notification_bp.route('/', methods=['POST'])
@login_required
def create():
    form = NotificationRuleForm()
    if form.validate_on_submit():
        notification = NotificationRule(
            detector_id=form.detector_id.data,
            message_template_id=form.message_template_id.data,
            contact_id=form.contact_id.data,
            permission_id=session.get('permission_id')            
        )
        db.session.add(notification)
        db.session.commit()
        flash('Notification rule added successfully!', 'success')
        # return Response(status=201)
        return redirect(url_for('notification.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@notification_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    notification = NotificationRule.query.get_or_404(id)
    form = NotificationRuleForm(obj=notification)
    if form.validate_on_submit():
        form.populate_obj(notification)
        db.session.commit()
        # return Response(status=200)
        return redirect(url_for('notification.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@notification_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    notification = NotificationRule.query.get_or_404(id)
    db.session.delete(notification)
    db.session.commit()
    # return Response(status=200)
    return redirect(url_for('notification.view'))
