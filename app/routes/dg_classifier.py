from flask import Blueprint, render_template, request, jsonify, session
import os
import uuid
from dg_classifier import DangerousGoodsAnalyzer

dg_classifier_bp = Blueprint('dg_classifier', __name__)
analyzer = DangerousGoodsAnalyzer()
PDF_FOLDER = 'user_pdf'
os.makedirs(PDF_FOLDER, exist_ok=True)

@dg_classifier_bp.before_request
def assign_user_uuid():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        print(f"Assigned new UUID: {session['user_id']}")

@dg_classifier_bp.route('/dg-classifier')
def view_dg():
    user_uuid = session.get('user_id')
    print(f"Current user UUID: {user_uuid}")
    
    return render_template('dg_classifier/index.html')

@dg_classifier_bp.route('/analyze-msds', methods=['POST'])
def analyze_msds():
    relevant_text = analyzer.get_relevant_chunks()
    print(relevant_text)
    llm_response = analyzer.get_llm_response(relevant_text)
    analyzer.delete_documents()

    print('response telah muncul dan dokumen telah di hapus')
    return jsonify({'Response': llm_response})

@dg_classifier_bp.route('/process-msds', methods=['POST'])
def process_uploaded_msds():
    user_id = session['user_id']

    if 'file' not in request.files:
        return jsonify({'Response': 'Tolong upload file PDF'}), 400

    file = request.files['file']
    file_path = os.path.join(PDF_FOLDER, file.filename)
    
    if file.filename in os.listdir(PDF_FOLDER):
        print('File already exists in', PDF_FOLDER)
        os.remove(file_path)

    file.save(file_path)
    print('File saved to', file_path)
    
    analyzer.process_document(file_path, user_id)

    return jsonify({'Response': 'MSDS processing success'}), 200
