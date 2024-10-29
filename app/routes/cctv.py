from flask import render_template, redirect, url_for, flash, session, Response, Blueprint, jsonify, abort
from flask_login import login_required
from app.models import CCTV, CCTVLocation, Detector
from app import db
from app.forms import AddCCTVForm, CCTVForm, EditCCTVForm
import cv2
import logging
from flasgger import swag_from

from utils.auth import get_allowed_permission_ids

# Configure logging
logging.basicConfig(level=logging.DEBUG)

cctv_api_docs = {
    "view" : {
        "parameters": [
            {
                "name": "id",
                "in": "path",
                "type": "integer",
                "required": False,
                "description": "Numeric ID of the CCTV to get"
            }
        ],
        "definitions": {
            "CCTV": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer"
                    },
                    "location": {
                        "type": "string"
                    },
                    "type": {
                        "type": "string"
                    },
                    "ip_address": {
                        "type": "string"
                    },
                    "status": {
                        "type": "integer"
                    }
                }
            }
        },
        "responses": {
            "200": {
                "description": "A list of CCTVs or a specific CCTV",
                "schema": {
                    "$ref": "#/definitions/CCTV"
                }
            },
            "404": {
                "description": "CCTV not found"
            }
        }
    },
    "create" : {
        "parameters": [
            {
                "name": "location",
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "Location of the CCTV"
            },
            {
                "name": "type",
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "Type of the CCTV"
            },
            {
                "name": "ip_address",
                "in": "formData",
                "type": "string",
                "required": True,
                "description": "IP address of the CCTV"
            }
        ],
        "responses": {
            "201": {
                "description": "CCTV added successfully"
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
                "description": "Numeric ID of the CCTV to edit"
            }
        ],
        "responses": {
            "200": {
                "description": "CCTV edited successfully"
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
                "description": "Numeric ID of the CCTV to delete"
            }
        ],
        "responses": {
            "200": {
                "description": "CCTV deleted successfully"
            }
        }
    },
    "stream" : {
        "parameters": [
            {
                "name": "cctv_id",
                "in": "path",
                "type": "integer",
                "required": True,
                "description": "Numeric ID of the CCTV to stream"
            }
        ],
        "responses": {
            "200": {
                "description": "CCTV stream"
            }
        }
    }
}

cctv_bp = Blueprint('cctv', __name__, url_prefix='/cctv')

# CCTV    
@cctv_bp.route('/', methods=['GET'])
@cctv_bp.route('/<int:id>', methods=['GET'])
@login_required
def view(id=None):
    logging.debug(f"Permission ID: {session.get('permission_id')}")
    form = CCTVForm()    
    form.location_id.choices.insert(0, (0, "Select Location"))
    if id:
        cctv = CCTV.query.get_or_404(id)
        # cctv = {
        #     'id': cctv.id,
        #     'location': cctv.location,
        #     'type': cctv.type,
        #     'ip_address': cctv.ip_address,
        #     'status': cctv.status
        # }
        return jsonify(cctv), 200             
    else:
        # cctvs = []
        # for cctv in CCTV.query.filter(CCTV.permission_id == session.get('permission_id')).all():
        #     detectors = Detector.query.filter(Detector.cctv_id == cctv.id).all()
        #     cctvs.append({
        #         'id': cctv.id, 
        #         'location': cctv.location, 
        #         'type': cctv.type, 
        #         'ip_address': cctv.ip_address, 
        #         'status': cctv.status,
        #         'is_used': len(detectors) > 0
        #     })        
        cctvs = CCTV.query.filter(CCTV.permission_id == session.get('permission_id')).all()
        # return jsonify(cctvs), 200
        return render_template('manage_cctv.html', cameras=cctvs, form=form)

@cctv_bp.route('/', methods=['POST'])
@login_required
def create():
    form = CCTVForm()    
    if form.location_id.data == 0:
        if form.location_name.data is None or form.location_name.data == "":
            flash("Please select a location!", "danger")
            return redirect(url_for("admin.menu"))            
        else:
            location = CCTVLocation(name=form.location_name.data)
            db.session.add(location)
            db.session.commit()
            location_id = location.id
    else:
        location_id = form.location_id.data

    if form.is_submitted():
        cctv = CCTV(
            cctv_location_id=location_id,
            type=form.type.data, 
            ip_address=form.ip_address.data, 
            status=0, 
            permission_id=session.get('permission_id')
        )
        db.session.add(cctv)
        db.session.commit()
        flash('CCTV added successfully!', 'success')
        # return Response(status=201)
        return redirect(url_for('cctv.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@cctv_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    cctv = CCTV.query.get_or_404(id)
    form = CCTVForm(obj=cctv)
    logging.debug(f"Form data: {form.data}")

    if form.location_id.data == 0:
        if form.location_name.data is None or form.location_name.data == "":
            flash("Please select a location!", "danger")
            return redirect(url_for("admin.menu"))            
        else:
            location = CCTVLocation(name=form.location_name.data)
            db.session.add(location)
            db.session.commit()
            location_id = location.id
    else:
        location_id = form.location_id.data

    if form.is_submitted():
        logging.debug(f"Form validated: {form.data}")
        cctv.cctv_location_id = location_id
        cctv.type = form.type.data
        cctv.ip_address = form.ip_address.data
        cctv.status = form.status.data
        cctv.permission_id = session.get('permission_id')
        db.session.commit()
        flash('CCTV edited successfully!', 'success')
        # return Response(status=204)
        return redirect(url_for('cctv.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@cctv_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    logging.debug(f"Deleting CCTV with ID: {id}")
     # Check if there are any detectors using this CCTV
    if Detector.query.filter_by(cctv_id=id).first():
        flash('Cannot delete CCTV. It is currently in use by a detector.', 'error')
        return redirect(url_for('cctv.view'))
    
    cctv = CCTV.query.get_or_404(id)
    db.session.delete(cctv)
    db.session.commit()
    flash('CCTV deleted successfully!', 'success')

@cctv_bp.route('/<int:cctv_id>/stream')
@login_required
def stream(cctv_id):
    cctv = CCTV.query.get_or_404(cctv_id)
    def generate_frames():
        address = 0 if cctv.ip_address == "http://0.0.0.0" else cctv.ip_address            
        cap = cv2.VideoCapture(address)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
