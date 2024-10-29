import logging
from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, session, Response, jsonify
from flask_login import login_required
from app.models import Contact
from app import db, swagger
from app.forms import ContactForm
from utils.auth import get_allowed_permission_ids
from flasgger import swag_from

logging.basicConfig(level=logging.DEBUG)

contact_api_docs = {
    "view" : {
        "parameters": [
            {
                "name": "id",
                "in": "path",
                "type": "integer",
                "required": False,
                "description": "Numeric ID of the contact to get"
            }
        ],
        "definitions": {
            "Contact": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer"
                    },
                    "phone_number": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "description": {
                        "type": "string"
                    }
                }
            }
        },
        "responses": {
            "200": {
                "description": "A list of contacts or a specific contact",
                "schema": {
                    "$ref": "#/definitions/Contact"
                }
            },
            "404": {
                "description": "Contact not found"
            }
        }
    },
    "create" : {
        "parameters": [
            {
                "name": "phone_number",
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "Phone number of the contact"
            },
            {
                "name": "name",
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "Name of the contact"
            },
            {
                "name": "description",
                "in": "formData",
                "type": "string",
                "required": False,
                "description": "Description of the contact"
            }
        ],
        "responses": {
            "201": {
                "description": "Contact added successfully"
            },
            "400": {
                "description": "Bad request"
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
                "description": "Numeric ID of the contact to edit"
            },
            {
                "name": "phone_number",
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "Phone number of the contact"
            },
            {
                "name": "name",
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "Name of the contact"
            },
            {
                "name": "description",
                "in": "formData",
                "type": "string",
                "required": False,
                "description": "Description of the contact"
            }
        ],
        "responses": {
            "200": {
                "description": "Contact updated successfully"
            },
            "400": {
                "description": "Bad request"
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
                "description": "Numeric ID of the contact to delete"
            }
        ],
        "responses": {
            "200": {
                "description": "Contact deleted successfully"
            }
        }
    }
}

contact_bp = Blueprint('contact', __name__, url_prefix='/contact')

# CONTACT
@contact_bp.route('/', methods=['GET'])
@contact_bp.route('/<int:id>', methods=['GET'])
@swag_from(contact_api_docs['view'])
@login_required
def view(id=None):
    form = ContactForm()
    if id:        
        contact = Contact.query.get_or_404(id)
        contact = {
            'id': contact.id,
            'phone_number': contact.phone_number,
            'name': contact.name,
            'description': contact.description
        }
        return jsonify(contact), 200        
    else:
        contacts = []
        for contact in Contact.query.filter(Contact.permission_id == session.get('permission_id')).all():
            contacts.append({
                'id': contact.id,
                'phone_number': contact.phone_number,
                'name': contact.name,
                'description': contact.description
            })        
        return jsonify(contacts), 200
        # return render_template('manage_contact.html', whas=contacts, form=form)
    
@contact_bp.route('/', methods=['POST'])
@swag_from(contact_api_docs['create'])
@login_required
def create():
    form = ContactForm()
    if form.validate_on_submit():
        contact = Contact(
            phone_number=form.phone_number.data,
            name=form.name.data,
            description=form.description.data,
            permission_id=session.get('permission_id')
        )
        db.session.add(contact)
        db.session.commit()
        flash('Contact added successfully!')
        return Response(status=201)
        # return redirect(url_for('contact.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)


@contact_bp.route('/<int:id>/edit', methods=['POST'])
@swag_from(contact_api_docs['edit'])
@login_required
def edit(id):
    contact = Contact.query.get_or_404(id)
    form = ContactForm(obj=contact)
    if form.validate_on_submit():
        form.populate_obj(contact)
        db.session.commit()
        flash('Contact updated successfully!')
        return Response(status=200)
        # return redirect(url_for('contact.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@contact_bp.route('/<int:id>/delete', methods=['POST'])
@swag_from(contact_api_docs['delete'])
@login_required
def delete(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted successfully!')
    return Response(status=200)
    # return redirect(url_for('contact.view'))