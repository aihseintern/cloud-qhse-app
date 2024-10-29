import logging
from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, session, Response, jsonify
from flask_login import login_required
from app.models import Contact
from app import db, swagger
from app.forms import ContactForm
from utils.auth import get_allowed_permission_ids
from flasgger import swag_from

logging.basicConfig(level=logging.DEBUG)


contact_bp = Blueprint('contact', __name__, url_prefix='/contact')

# CONTACT
@contact_bp.route('/', methods=['GET'])
@contact_bp.route('/<int:id>', methods=['GET'])
@login_required
def view(id=None):
    form = ContactForm()
    if id:        
        contact = Contact.query.get_or_404(id)
        contact = {
            'id': contact.id,
            'phone_number': contact.phone_number,
            'name': contact.name,
            'description': contact.description,
            'is_group': contact.is_group
        }
        return jsonify(contact), 200        
    else:
        contacts = []
        for contact in Contact.query.filter(Contact.permission_id == session.get('permission_id')).all():
            contacts.append({
                'id': contact.id,
                'phone_number': contact.phone_number,
                'name': contact.name,
                'description': contact.description,
                'is_group': contact.is_group
            })        
        # return jsonify(contacts), 200
        return render_template('manage_contact.html', whas=contacts, form=form)
    
@contact_bp.route('/', methods=['POST'])
@login_required
def create():
    form = ContactForm()
    if form.validate_on_submit():
        contact = Contact(
            phone_number=form.phone_number.data,
            name=form.name.data,
            description=form.description.data,
            permission_id=session.get('permission_id'),
            is_group = (form.phone_number.data is None or form.phone_number.data == "")
        )
        db.session.add(contact)
        db.session.commit()
        flash('Contact added successfully!', 'success')
        # return Response(status=201)
        return redirect(url_for('contact.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)


@contact_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    contact = Contact.query.get_or_404(id)
    form = ContactForm(obj=contact)
    if form.validate_on_submit():
        form.populate_obj(contact)
        db.session.commit()
        flash('Contact updated successfully!', 'success')
        # return Response(status=200)
        return redirect(url_for('contact.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@contact_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted successfully!', 'success')
    # return Response(status=200)
    return redirect(url_for('contact.view'))
