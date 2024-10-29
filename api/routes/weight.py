import os
from datetime import datetime
from base64 import b64encode
from flask import Blueprint, Response, abort, render_template, redirect, url_for, flash, session, jsonify
from flask_login import login_required
from app.models import DetectorType, Weight
from app import db
from app.forms import ModelForm
import logging
from flasgger import swag_from

from utils.auth import get_allowed_permission_ids

logging.basicConfig(level=logging.DEBUG)

weight_api_docs = {
    "view" : {
        "parameters": [
            {
                "name": "id",
                "in": "path",
                "type": "integer",
                "required": False,
                "description": "Numeric ID of the weight to get"
            }
        ],
        "definitions": {
            "Weight": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer"
                    },
                    "name": {
                        "type": "string"
                    },
                    "detector_type_id": {
                        "type": "integer"
                    },
                    "file": {
                        "type": "string"
                    },
                    "path": {
                        "type": "string"
                    },
                    "created_at": {
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
                "description": "A list of weights or a specific weight",
                "schema": {
                    "$ref": "#/definitions/Weight"
                }
            },
            "404": {
                "description": "Weight not found"
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
                "description": "Name of the weight"
            },
            {
                "name": "detector_type",
                "in": "formData",
                "type": "integer",
                "required": True,
                "description": "ID of the detector type"
            },
            {
                "name": "file",
                "in": "formData",
                "type": "file",
                "required": True,
                "description": "Weight file"
            }
        ],
        "responses": {
            "201": {
                "description": "Weight added successfully"
            },
            "400": {
                "description": "Invalid data"
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
                "description": "Numeric ID of the weight to edit"
            },
            {
                "name": "name",
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "Name of the weight"
            },
            {
                "name": "detector_type",
                "in": "formData",
                "type": "integer",
                "required": True,
                "description": "ID of the detector type"
            },
            {
                "name": "file",
                "in": "formData",
                "type": "file",
                "required": True,
                "description": "Weight file"
            }
        ],
        "responses": {
            "200": {
                "description": "Weight updated successfully"
            },
            "400": {
                "description": "Invalid data"
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
                "description": "Numeric ID of the weight to delete"
            }
        ],
        "responses": {
            "204": {
                "description": "Weight deleted successfully"
            }
        }
    }
}   

weight_bp = Blueprint('weight', __name__, url_prefix='/weight')

# MODEL
@weight_bp.route('/', methods=['GET'])
@weight_bp.route('/<int:id>', methods=['GET'])
@swag_from(weight_api_docs['view'])
@login_required
def view(id=None):
    if id:
        weight = Weight.query.get_or_404(id)
        weight = {
            'id': weight.id,
            'name': weight.name,
            'detector_type_id': weight.detector_type_id,
            'file': weight.file,
            'path': weight.path,
            'created_at': weight.created_at,
            'permission_id': weight.permission_id
        }
        return jsonify(weight), 200
    else:
        weights = []
        for weight in Weight.query.filter(Weight.permission_id == session.get('permission_id')).all():
            weights.append({
                'id': weight.id,
                'name': weight.name,
                'detector_type_id': weight.detector_type_id,
                'file': weight.file,
                'path': weight.path,
                'created_at': weight.created_at,
                'permission_id': weight.permission_id
            })        
        return jsonify(weights), 200
        # weights = Weight.query.filter(Weight.permission_id == session.get('permission_id')).all()
        # return render_template('manage_model.html', models=weights, form=ModelForm())
    
@weight_bp.route('/', methods=['POST'])
@swag_from(weight_api_docs['create'])
@login_required
def create():
    form = ModelForm()
    if form.validate_on_submit():
        permission_id_dir = os.path.join('weights', session.get('permission_id'))
        if not os.path.exists(permission_id_dir):
            os.makedirs(permission_id_dir)
        form.file.data.save(os.path.join(permission_id_dir, form.file.data.filename))
        new_model = Weight(
            name=form.name.data,
            detector_type_id=form.detector_type.data,
            file=form.file.data.read(),
            path=os.path.join(permission_id_dir, form.file.data.filename),
            created_at=datetime.now(),
            permission_id=session.get('permission_id')
        )
        db.session.add(new_model)
        db.session.commit()
        flash('Model added successfully!')
        return Response(status=201)
        # return redirect(url_for('weight.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@weight_bp.route('/<int:id>/edit', methods=['POST'])
@swag_from(weight_api_docs['edit'])
@login_required
def edit(id):
    model = Weight.query.get_or_404(id)
    form = ModelForm(obj=model)
    if form.validate_on_submit():
        model.name = form.name.data
        model.detector_type_id = form.detector_type.data
        model.file = form.file.data.read()
        model.path = os.path.join('weights', session.get('permission_id'), form.file.data.filename)
        model.created_at = datetime.now()
        model.permission_id = session.get('permission_id')
        db.session.commit()
        flash('Model updated successfully!')
        return Response(status=200)
        # return redirect(url_for('weight.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@weight_bp.route('/<int:id>/delete', methods=['POST'])
@swag_from(weight_api_docs['delete'])
@login_required
def delete(id):
    model = Weight.query.get_or_404(id)
    db.session.delete(model)
    db.session.commit()
    return Response(status=204)
    # return redirect(url_for('weight.view'))

