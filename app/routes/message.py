import logging
from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, session, Response, jsonify
from flask_login import login_required
from app.models import MessageTemplate
from app import db
from app.forms import MessageTemplateForm
from utils.auth import get_allowed_permission_ids
from flasgger import swag_from

logging.basicConfig(level=logging.DEBUG)

message_bp = Blueprint('message', __name__, url_prefix='/message')

# MESSAGE
@message_bp.route('/', methods=['GET'])
@message_bp.route('/<int:id>', methods=['GET'])
@login_required
def view(id=None):
    logging.debug(f"Permission ID: {session.get('permission_id')}")
    if id:
        message = MessageTemplate.query.get_or_404(id)
        message = {
            'id': message.id,
            'name': message.name,
            'template': message.template,
            'permission_id': message.permission_id
        }
        return jsonify(message), 200
    else:
        messages = []
        for message in MessageTemplate.query.filter(MessageTemplate.permission_id == session.get('permission_id')).all():
            messages.append({
                'id': message.id,
                'name': message.name,
                'template': message.template,
                'permission_id': message.permission_id
            })        
        return jsonify(messages), 200
        # return render_template('manage_message.html', messages=messages, form=MessageTemplateForm())
    
@message_bp.route('/', methods=['POST'])    
@login_required
def create():
    form = MessageTemplateForm()
    if form.validate_on_submit():
        message = MessageTemplate(
            name=form.name.data,
            template=form.template.data,
            permission_id=session.get('permission_id')
        )
        db.session.add(message)
        db.session.commit()
        flash('Message template added successfully!', 'success')
        # return Response(status=201)
        # return redirect(url_for('message.view'))
        return redirect(url_for('notification.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@message_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    message = MessageTemplate.query.get_or_404(id)
    form = MessageTemplateForm(obj=message)
    if form.validate_on_submit():
        form.populate_obj(message)
        db.session.commit()
        return Response(status=200)
        # return redirect(url_for('message.view'))
        # return redirect(url_for('notification.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@message_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    message = MessageTemplate.query.get_or_404(id)
    db.session.delete(message)
    db.session.commit()
    # return Response(status=200)   
    return redirect(url_for('notification.view'))
