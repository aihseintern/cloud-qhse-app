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

notification_api_docs = {
    "view" : {
        "parameters": [
            {
                "name": "id",
                "in": "path",
                "type": "integer",
                "required": False,
                "description": "Numeric ID of the notification to get"
            }
        ],
        "definitions": {
            "Notification": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer"
                    },
                    "name": {
                        "type": "string"
                    },
                    "description": {
                        "type": "string"
                    },
                    "permission_id": {
                        "type": "string"
                    }
                }
            }
        },
        "responses": {
            "200": {
                "description": "A list of notifications or a specific notification",
                "schema": {
                    "$ref": "#/definitions/Notification"
                }
            },
            "404": {
                "description": "Notification not found"
            }
        }
    },
    "create" : {
        "parameters": [
            {
                "name": "name",
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "Name of the notification"
            },
            {
                "name": "description",
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "Description of the notification"
            }
        ],
        "responses": {
            "201": {
                "description": "Notification rule created"
            },
            "400": {
                "description": "Form validation failed"
            }
        }
    },
    "edit" : {
        "parameters": [
            {
                "name": "id",
                "in": "path",
                "type": "integer",
                "required": True,
                "description": "Numeric ID of the notification to edit"
            },
            {
                "name": "name",
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "Name of the notification"
            },
            {
                "name": "description",
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "Description of the notification"
            }
        ],
        "responses": {
            "200": {
                "description": "Notification rule edited"
            },
            "400": {
                "description": "Form validation failed"
            }
        }
    },
    "delete" : {
        "parameters": [
            {
                "name": "id",
                "in": "path",
                "type": "integer",
                "required": True,
                "description": "Numeric ID of the notification to delete"
            }
        ],
        "responses": {
            "200": {
                "description": "Notification rule deleted"
            }
        }
    }
}

notification_bp = Blueprint('notification', __name__, url_prefix='/notification')

# NOTIFICATION
@notification_bp.route('/', methods=['GET'])
@notification_bp.route('/<int:id>', methods=['GET'])
@swag_from(notification_api_docs['view'])
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
        notifications = []
        for notification in NotificationRule.query.filter(NotificationRule.permission_id == session.get('permission_id')).all():
            notifications.append({
                'id': notification.id,
                'detector_id': notification.detector_id,
                'message_template_id': notification.message_template_id,
                'contact_id': notification.contact_id,
                'permission_id': notification.permission_id
            })        
        return jsonify(notifications), 200        
        # return render_template('manage_notification_rules.html', messages=messages, rules=notifications, rule_form=NotificationRuleForm(), message_form=MessageTemplateForm())
    
@notification_bp.route('/', methods=['POST'])
@swag_from(notification_api_docs['create'])
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
        flash('Notification rule added successfully!')
        return Response(status=201)
        # return redirect(url_for('notification.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@notification_bp.route('/<int:id>/edit', methods=['POST'])
@swag_from(notification_api_docs['edit'])
@login_required
def edit(id):
    notification = NotificationRule.query.get_or_404(id)
    form = NotificationRuleForm(obj=notification)
    if form.validate_on_submit():
        form.populate_obj(notification)
        db.session.commit()
        return Response(status=200)
        # return redirect(url_for('notification.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@notification_bp.route('/<int:id>/delete', methods=['POST'])
@swag_from(notification_api_docs['delete'])
@login_required
def delete(id):
    notification = NotificationRule.query.get_or_404(id)
    db.session.delete(notification)
    db.session.commit()
    return Response(status=200)
    # return redirect(url_for('notification.view'))
