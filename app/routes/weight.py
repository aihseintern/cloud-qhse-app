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

weight_bp = Blueprint('weight', __name__, url_prefix='/weight')

# MODEL
@weight_bp.route('/', methods=['GET'])
@weight_bp.route('/<int:id>', methods=['GET'])
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
        # weights = []
        # for weight in Weight.query.filter(Weight.permission_id == session.get('permission_id')).all():
        #     weights.append({
        #         'id': weight.id,
        #         'name': weight.name,
        #         'detector_type_id': weight.detector_type_id,
        #         'file': weight.file,
        #         'path': weight.path,
        #         'created_at': weight.created_at,
        #         'permission_id': weight.permission_id
        #     })        
        # return jsonify(weights), 200
        weights = Weight.query.filter(Weight.permission_id == session.get('permission_id')).all()
        form = ModelForm()
        form.detector_type_id.choices.insert(0, (0, 'Select Detector Type'))
        return render_template('manage_model.html', models=weights, form=form)
    
@weight_bp.route('/', methods=['POST'])
@login_required
def create():
    form = ModelForm()
    if form.detector_type_id.data == 0:
            if form.detector_type_name.data is None or form.detector_type_name.data == "":
                flash("Please select a detector type!", "danger")
                return redirect(url_for("weight.view"))            
            else:
                detector_type = DetectorType(name=form.detector_type_name.data)
                db.session.add(detector_type)
                db.session.commit()
                detector_type_id = detector_type.id
    else:
        detector_type_id = form.detector_type_id.data

    if form.is_submitted():
        permission_id_dir = os.path.join('weights', session.get('permission_name'))
        print("permission_id_dir:", permission_id_dir)
        if not os.path.exists(permission_id_dir):
            os.makedirs(permission_id_dir)
        file_path = os.path.join(permission_id_dir, form.file.data.filename)
        form.file.data.save(file_path)
        new_model = Weight(
            name=form.name.data,
            detector_type_id=detector_type_id,
            file=form.file.data.read(),
            path=file_path,
            created_at=datetime.now(),
            permission_id=session.get('permission_id')
        )
        db.session.add(new_model)
        db.session.commit()
        flash('Model added successfully!', 'success')
        # return Response(status=201)
        return redirect(url_for('weight.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@weight_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    model = Weight.query.get_or_404(id)
    form = ModelForm(obj=model)
    if form.file.data:
        WEIGHTS_FOLDER = os.path.join(os.getcwd(), 'weights')
        permission_id_dir = os.path.join(WEIGHTS_FOLDER, session.get('permission_name'))
        print("permission_id_dir:", permission_id_dir)
        if not os.path.exists(permission_id_dir):
            os.makedirs(permission_id_dir)
        file_path = os.path.join(permission_id_dir, form.file.data.filename)        
        form.file.data.save(file_path)
        model_file = form.file.data.read()
    else:
        model_file = model.file
        file_path = model.path

    if form.detector_type_id.data == 0:
        if form.detector_type_name.data is None or form.detector_type_name.data == "":
            flash("Please select a detector type!", "danger")
            return redirect(url_for("weight.view"))            
        else:
            detector_type = DetectorType(name=form.detector_type_name.data)
            db.session.add(detector_type)
            db.session.commit()
            detector_type_id = detector_type.id
    else:
        detector_type_id = form.detector_type_id.data

    if form.is_submitted():
        model.name = form.name.data
        model.detector_type_id = detector_type_id
        model.file = model_file
        model.path = file_path
        model.permission_id = session.get('permission_id')
        db.session.commit()
        flash('Model updated successfully!', 'success')
        # return Response(status=200)
        return redirect(url_for('weight.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@weight_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    model = Weight.query.get_or_404(id)
    db.session.delete(model)
    db.session.commit()
    # return Response(status=204)
    return redirect(url_for('weight.view'))

