import time
import cv2
import logging
from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, session, Response, jsonify
from flask_login import login_required
from app.models import CCTV, Detector, DetectorType, Weight
from app import db
from app.forms import DetectorForm
from utils.auth import get_allowed_permission_ids
from flasgger import swag_from

logging.basicConfig(level=logging.DEBUG)

detector_bp = Blueprint('detector', __name__, url_prefix='/detector')

# DETECTOR
@detector_bp.route('/', methods=['GET'])
@detector_bp.route('/<int:id>', methods=['GET'])
@login_required
def view(id=None):
    if id:
        detector = Detector.query.get_or_404(id)
        detector = {
            'id': detector.id,
            'cctv_id': detector.cctv_id,
            'weight_id': detector.weight_id,
            'running': detector.running,
            'permission_id': detector.permission_id
        }
        return jsonify(detector), 200
    else:
        # detectors = []
        # for detector in Detector.query.filter(Detector.permission_id == session.get('permission_id')).all():
        #     detectors.append({
        #         'id': detector.id,
        #         'cctv_id': detector.cctv_id,
        #         'weight_id': detector.weight_id,
        #         'running': detector.running,
        #         'permission_id': detector.permission_id
        #     })        
        detectors = Detector.query.filter(Detector.permission_id == session.get('permission_id')).order_by(Detector.id).all()
        # return jsonify(detectors), 200
        return render_template('manage_detector.html', detectors=detectors, form=DetectorForm())

@detector_bp.route('/', methods=['POST'])
@login_required
def create():
    form = DetectorForm()
    if form.validate_on_submit():
        detector = Detector(
            cctv_id=form.cctv_id.data,
            weight_id=form.weight_id.data,
            running=form.running.data,
            permission_id=session.get('permission_id')
        )
        db.session.add(detector)
        db.session.commit()
        flash('Detector added successfully!', 'success')
        # return Response(status=201)
        return redirect(url_for('detector.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@detector_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit(id):
    detector = Detector.query.get_or_404(id)
    form = DetectorForm(obj=detector)
    if form.validate_on_submit():
        logging.debug(f"Form data: {form.running.data}")
        detector.cctv_id = form.cctv_id.data or detector.cctv_id
        detector.weight_id = form.weight_id.data or detector.weight_id
        detector.running = bool(int(form.running.data))
        db.session.commit()
        flash('Detector updated successfully!', 'success')
        # return Response(status=200)
        return redirect(url_for('detector.view'))
    else:
        logging.debug(f"Form validation failed: {form.errors}")
    abort(400)

@detector_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    detector = Detector.query.get_or_404(id)
    db.session.delete(detector)
    db.session.commit()
    flash('Detector deleted successfully!', 'success')
    # return Response(status=204)
    return redirect(url_for('detector.view'))

@detector_bp.route('/<int:detector_id>/stream')
@login_required
def detector_stream(detector_id):
    from utils.detector import annotated_frames
    def generate_frames():
        while True:
            if detector_id in annotated_frames:
                frame = annotated_frames[detector_id]
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                time.sleep(0.01)  # Wait for a short time before checking again

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')