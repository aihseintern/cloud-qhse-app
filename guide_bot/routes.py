# guide_bot/routes.py
from collections import defaultdict
from functools import wraps
import io
import re
from uuid import uuid4
import uuid
from flask import Blueprint, abort, render_template, redirect, send_file, send_from_directory, url_for, flash, request, session
from langchain_chroma import Chroma
import markdown
from app.auth import otp_required
from app.models import Document, DocumentPermission, Permission, UserPermission
from guide_bot.forms import DocumentForm, NewFolderForm, EditFileForm
from app import db

from langchain_huggingface import HuggingFaceEmbeddings
import os
from langchain_core.documents import Document as ChatDocument
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from guide_bot import conversation_chat, create_conversational_chain, load_vector_store, save_uploaded_file, load_saved_files, split_documents, extract_text_from_file, embeddings
from utils.auth import get_allowed_permission_ids

guide_bot = Blueprint('guide_bot', __name__)

GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY')

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*\t\n]', '_', filename)

# Don't forget to update the manage_documents route to save documents with their ids
# @guide_bot.route('/guide-bot/documents', methods=['GET', 'POST'])
# @login_required
# # def manage_documents():
#     file_form = DocumentFileForm()
#     folder_form = DocumentFolderForm()
    
#     # Ambil page dan items_per_page dari parameter query, default page=1 dan per_page=10
#     page = request.args.get('page', 1, type=int)
#     items_per_page = request.args.get('items_per_page', 10, type=int)
    
#     # Ambil query pencarian dari parameter query
#     search_query = request.args.get('search_query', '', type=str)

#     # Get the current user's role
#     user_role = permission_id
    
#     # Filter dokumen berdasarkan search query jika ada
#     if search_query:
#         documents = Document.query.filter(Document.title.ilike(f'%{search_query}%')).paginate(page=page, per_page=items_per_page)
#     else:
#         documents = Document.query.paginate(page=page, per_page=items_per_page)
    
#     # Proses penambahan dokumen
#     if file_form.validate_on_submit() or folder_form.validate_on_submit():
#         files = request.files.getlist('files')
#         allowed_roles = ','.join(file_form.allowed_roles.data)
#         for file in files:
#             filename = secure_filename(file.filename)
#             new_document = Document(title=filename, file=file.read(), allowed_roles=allowed_roles)
#             db.session.add(new_document)
#             db.session.commit()

#             # Save the file to disk with its document ID
#             save_dir = 'data'
#             if not os.path.exists(save_dir):
#                 os.makedirs(save_dir)
#             file_path = os.path.join(save_dir, f"{filename}")
#             with open(file_path, 'wb') as f:
#                 f.write(new_document.file)

#         flash('Document added successfully!')
#         return redirect(url_for('guide_bot.manage_documents', page=page, items_per_page=items_per_page, search_query=search_query))

#     # Proses penambahan dokumen
#     if folder_form.validate_on_submit():
#         files = request.files.getlist('files')
#         allowed_roles = ','.join(folder_form.allowed_roles.data)  # Handle roles similarly for folder form
#         for file in files:
#             filename = secure_filename(file.filename)
#             # Simpan dokumen dalam database
#             new_document = Document(title=filename, file=file.read(), allowed_roles=allowed_roles)
#             db.session.add(new_document)
#             db.session.commit()

#             # Save the file to disk with its document ID
#             save_dir = 'data'
#             if not os.path.exists(save_dir):
#                 os.makedirs(save_dir)
#             file_path = os.path.join(save_dir, f"{filename}")
#             with open(file_path, 'wb') as f:
#                 f.write(new_document.file)

#         # flash('Document added successfully!')
#         # return redirect(url_for('guide_bot.manage_documents', page=page, items_per_page=items_per_page, search_query=search_query))
    
#     # Render halaman dengan form dan dokumen terpaginate
#     return render_template('guide_bot/manage_documents.html', 
#                            file_form=file_form, 
#                            folder_form=folder_form, 
#                            documents=documents, 
#                            items_per_page=items_per_page, 
#                            search_query=search_query,
#                            user_role=user_role)

UPLOAD_FOLDER = 'uploads'

def get_file_structure_db(current_dir, document_dirs):
    """Membuat struktur file dari document_dirs di dalam current_dir"""
    file_structure = {}
    dirs = []
    files = []
    print('ROOT: ', '/'.join(current_dir.split('/')[1:]))

    if not document_dirs:
        for dir in document_dirs:
            if '/'.join(dir.split('/')[:-1]) == '/'.join(current_dir.split('/')[1:]):        
                files.append(dir.split('/')[-1])
            elif len(dir.split('/')) > 0 and dir.split('/')[0] not in dirs:
                dirs.append(dir.split('/')[0])
            print('/'.join(dir.split('/')[:-1]))

        file_structure[''] = {'dirs': dirs, 'files': files}
        # print("File structure from DB:", file_structure)
    return file_structure

def get_file_structure(root_dir):
    """Membuat struktur file hanya di level direktori saat ini"""
    file_structure = {}
    
    # Hanya melihat isi dari direktori root tanpa masuk ke subfolder
    with os.scandir(root_dir) as entries:
        dirs = []
        files = []
        for entry in entries:
            if entry.is_dir():
                dirs.append(entry.name)
            elif entry.is_file():
                files.append(entry.name)
        file_structure[''] = {'dirs': dirs, 'files': files}
    # print("File structure:", file_structure)
    return file_structure

def save_file(current_dir, file, permission_id=None):
    """Menyimpan file ke subdirektori yang sesuai"""

def get_next_folder(current_dir, document_dirs):
    # Set to hold unique folder names from the paths
    next_folders = set()
    
    # Iterate over all document directories
    print("Document dirs:", document_dirs)  
    if document_dirs:
        for doc_dir in document_dirs:
            print("Comparing:", doc_dir, current_dir)
            # Check if the path starts with the current directory
            if doc_dir.startswith(current_dir):
                print("Found:", doc_dir)
                # Get the relative path after the current directory
                relative_path = doc_dir[len(current_dir):].strip('/')
                print("Relative path:", relative_path)
                # Split the relative path into parts
                path_parts = relative_path.split('/')
                print("Path parts:", path_parts)
                # If there's at least one part, the first part is the next folder
                if len(path_parts) > 1:
                    next_folders.add(path_parts[0])

        # Return next folders as sorted list
    return sorted(next_folders)

def create_folder(current_dir, folder_name):
    """Membuat folder baru di direktori yang sesuai"""
    dirpath = os.path.join(current_dir, folder_name)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    
    index_path = os.path.join(dirpath, 'index')
    with open(index_path, 'w') as f:
        f.write(f"")
    new_document = Document(
        title="index",
        dir=index_path)
    
    db.session.add(new_document)
    db.session.commit()

# Custom decorator to require qhse privileges
def qhse_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the user has QHSE permissions
        user_permissions = get_allowed_permission_ids()
        qhse_permission = Permission.query.filter_by(name='QHSE').first()
        if qhse_permission.id not in user_permissions:
            flash('You do not have permission to access this page.', 'error')
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function    

@guide_bot.route('/guide-bot/documents/', methods=['GET', 'POST'])
@guide_bot.route('/guide-bot/documents/<path:subdir>', methods=['GET', 'POST'])
@login_required
@qhse_required
def manage_documents(subdir=''):
    new_folder_form = NewFolderForm()
    document_form = DocumentForm()

    # Ambil query pencarian dari parameter query
    search_query = request.args.get('search_query', '', type=str)

    if search_query:
        documents = Document.query.filter(Document.dir.ilike(f'%{search_query}%')).all()
        print("Documents:", documents)
        return render_template(
            'guide_bot/search_documents.html', 
            documents=documents, 
            subdir=subdir,
            new_folder_form=new_folder_form,
            document_form=document_form,            
            search_query=search_query)
    else:
        documents = Document.query.all()

    # Proses penambahan dokumen                
    if document_form.validate_on_submit():
        files = request.files.getlist('files')
        for file in files:
            if file and allowed_file(file.filename):                
                # Simpan file dengan full path sesuai struktur folder            
                file_dir = os.path.normpath(os.path.join(UPLOAD_FOLDER, subdir)) if subdir else UPLOAD_FOLDER
                file_path = os.path.normpath(os.path.join(file_dir, file.filename))
                filename = os.path.normpath(file.filename.split('/')[-1])

                print("File dir:", file_dir)
                print("File path:", file_path)
                print("Filename:", filename)

                # Cek apakah folder subdir ada, jika tidak buat folder
                os.makedirs(file_dir, exist_ok=True)
                dir_name = os.path.dirname(file_path)
                os.makedirs(dir_name, exist_ok=True)

                # Simpan file                
                file.save(file_path)

                # Simpan informasi dokumen di database
                new_document = Document(
                    title=filename, 
                    dir=os.path.normpath(os.path.join(subdir, file.filename)),
                )
                db.session.add(new_document)
                db.session.flush()

                print('Document permissions:', document_form.permission_id.data)
                document_permissions = document_form.permission_id.data
                if document_permissions:
                    for permission_id in document_permissions:
                        new_document_permission = DocumentPermission(
                            document_id=new_document.id,
                            permission_id=permission_id
                        )
                        db.session.add(new_document_permission)

        db.session.commit()
        flash('Document(s) added successfully!', 'success')
        return redirect(url_for('guide_bot.manage_documents', subdir=subdir, search_query=search_query))    

    # Proses penambahan folder
    if new_folder_form.validate_on_submit():
        folder_name = new_folder_form.folder_name.data
        folder_path = os.path.normpath(os.path.join(UPLOAD_FOLDER, subdir, folder_name)) if subdir else os.path.normpath(os.path.join(UPLOAD_FOLDER, folder_name))

        # Cek apakah folder subdir ada, jika tidak buat folder
        os.makedirs(folder_path, exist_ok=True)

        # Simpan informasi dokumen di database
        new_document = Document(
            title='index', 
            dir=os.path.normpath(os.path.join(subdir, folder_name, 'index')),
        )
        document_permissions = new_folder_form.permission_id.data
        if document_permissions:
            for permission_id in document_permissions:
                new_document_permission = DocumentPermission(
                    document_id=new_document.id,
                    permission_id=permission_id
                )
                db.session.add(new_document_permission)
        db.session.add(new_document)
        db.session.commit()

        return redirect(url_for('guide_bot.manage_documents', subdir=subdir, search_query=search_query))

    # Ambil semua dokumen dari database
    documents = Document.query.all()

    # Filter dokumen berdasarkan subdir sekarang
    current_path = os.path.normpath(subdir) if subdir else ''
    
    # Folder dan file yang ada di direktori ini
    folders = set()
    files = []

    # Loop melalui dokumen untuk mencari yang sesuai dengan subdir
    for doc in documents:
        doc_path_parts = doc.dir.split(os.sep)
        if current_path:
            # Jika ada subdir sekarang, pastikan dokumen ada di dalam subdir
            if not doc.dir.startswith(current_path):
                continue
            # Ambil bagian setelah subdir
            remaining_path = doc.dir[len(current_path)+1:]
        else:
            remaining_path = doc.dir
        
        # Cek apakah folder atau file
        if os.sep in remaining_path:
            # Tambahkan folder yang belum ada di daftar
            folder_name = remaining_path.split(os.sep)[0]
            folders.add(folder_name)
        else:
            # Ini adalah file di subdir sekarang
            files.append(doc)

    # Convert set ke list untuk penampilan
    folders = list(folders)

    # Render halaman file explorer
    active_dir = enumerate(subdir.split('/'))
    return render_template('guide_bot/manage_documents.html', 
                           folders=folders,
                           files=files,
                           current_dir=subdir,
                           new_folder_form=new_folder_form,
                           document_form=document_form,
                           subdir=subdir,
                           active_dir=active_dir)

UPLOAD_FOLDER = 'uploads'  # Tempat penyimpanan file yang diunggah
ALLOWED_EXTENSIONS = {
    'bmp', 'csv', 'doc', 'docx', 'eml', 'epub', 'heic', 'html', 'jpeg', 'png', 
    'md', 'msg', 'odt', 'org', 'p7s', 'pdf', 'ppt', 'pptx', 'rst', 'rtf', 
    'tiff', 'txt', 'tsv', 'xls', 'xlsx', 'xml'
}

# Fungsi untuk memeriksa ekstensi file yang diperbolehkan
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@guide_bot.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@guide_bot.route('/guide-bot/documents/edit/<int:id>', methods=['POST'])
@login_required
def edit_document(id):
    document = Document.query.get_or_404(id)
    new_name = request.get_json().get('new_name')
    
    if new_name:        
        document.title = new_name  
        src_path = document.dir
        dst_path = os.path.join('/'.join(document.dir.split('/')[:-1]), new_name)      
        os.rename(src_path, dst_path)
        document.dir = dst_path
        db.session.commit()
        flash('Document updated successfully!')
        return redirect(url_for('guide_bot.manage_documents', subdir=""))
    
    return redirect(url_for('guide_bot.manage_documents', subdir=""))

@guide_bot.route('/guide-bot/documents/delete-multiple', methods=['POST'])
@login_required
def delete_multiple_documents():
    document_ids = request.form.getlist('document_ids')  # Use getlist to handle multiple values

    if not document_ids:
        flash('No documents selected for deletion.', 'warning')
        return redirect(url_for('guide_bot.manage_documents'))
    
    if not current_user.is_manager():
        flash('You do not have permission to delete documents.', 'error')
        return redirect(url_for('guide_bot.manage_documents'))

    deleted_files = []
    not_found_files = []
    errors = []

    for doc_id in document_ids:
        if doc_id:  # Ensure id is not empty
            document = Document.query.get(doc_id)
            if document:
                db.session.delete(document)
                file_path = document.dir
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_files.append(file_path)
                    except Exception as e:
                        errors.append(f'Error removing file {file_path}: {e}')
                else:
                    not_found_files.append(file_path)
            else:
                flash(f'Document with ID {doc_id} not found.', 'warning')
    
    db.session.commit()

    if deleted_files:
        flash(f'Selected documents deleted successfully: {", ".join(deleted_files)}', 'success')
    if not_found_files:
        flash(f'Files not found: {", ".join(not_found_files)}', 'warning')
    if errors:
        flash(f'Errors occurred: {", ".join(errors)}', 'error')

    return redirect(url_for('guide_bot.manage_documents'))

@guide_bot.route('/guide-bot/documents/delete/<int:id>', methods=['POST'])
def delete_document(id):
    document = Document.query.get_or_404(id)
    
    # Delete the document from the database
    db.session.delete(document)
    db.session.commit()

    # delete the file from the server
    # file_path = os.path.join('data', secure_filename(document.title))
    file_path = document.dir
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Successfully deleted file: {file_path}")  # Debugging statement
        except Exception as e:
            print(f"Error removing file {file_path}: {e}")
    else:
        print(f"File not found: {file_path}")

    flash('Document deleted successfully!')
    return redirect(url_for('guide_bot.manage_documents', subdir=""))

@guide_bot.route('/guide-bot/documents/view/<int:id>')
@login_required
def view_document(id):
    document = Document.query.get_or_404(id)
    return render_template('guide_bot/view_document.html', document=document)
    # if current_user.is_manager() or document.is_accessible_by(current_user):
    #     return render_template('guide_bot/view_document.html', document=document)
    # else:
    #     flash('You do not have permission to view this document.', 'error')
    #     return redirect(url_for('guide_bot.manage_documents'))

@guide_bot.route('/guide-bot/document/file/<int:document_id>')
def get_document_file(document_id):
    document = Document.query.get_or_404(document_id)
    if document.dir:
        document_path = os.path.normpath(os.path.join(UPLOAD_FOLDER, document.dir))
        return send_file(document_path, as_attachment=True, download_name=document.title)
    else:
        abort(404)

@guide_bot.route('/guide-bot/documents/download/<int:id>')
def download_document(id):
    document = Document.query.get_or_404(id)
    return send_file(io.BytesIO(document.file), as_attachment=True, download_name=document.title)

@guide_bot.route('/aios')
@login_required
def index():
    return render_template('aios/base.html')

@guide_bot.before_request
def initialize_session():
    """Inisialisasi sesi jika belum ada, menggunakan before_request untuk efisiensi."""
    if 'history' not in session:
        session['history'] = []
        session['past_questions'] = []
        session['generated'] = ["Selamat datang di GuideBot!"]

@guide_bot.route('/guide-bot/chat', methods=['GET', 'POST'])
@guide_bot.route('/aios/guide-bot/chat', methods=['GET', 'POST'])
@login_required
def chat():
    # Jika GET, kembalikan halaman dengan riwayat pertanyaan
    if request.method == 'GET':
        return render_template(
            'guide_bot/index.html', 
            past=session.get('past_questions'), 
            generated=session.get('generated')
        )

    # Jika POST, proses input pengguna
    user_input = request.form.get('user_input')
    if not user_input:
        return {"error": "User input is required."}, 400

    # Tambahkan pertanyaan ke riwayat
    session['past_questions'].append(user_input)

    # Load vector store hanya jika belum ada (bisa di-cache)
    # user_permissions = UserPermission.query.filter(UserPermission.user_id == current_user.id).all()
    # permission_names = [user_permission.permission.name for user_permission in user_permissions]
    # for permission_name in permission_names:
    #     vector_store = load_vector_store(embeddings, permission_name)
    #     if not vector_store:
    #         return {"message": "No information available yet."}, 500

    #     # Merge soon
    vector_store = load_vector_store(embeddings)
    if not vector_store:
        return {"message": "No information available yet."}, 500

    # Buat conversational chain berdasarkan vector store
    chain = create_conversational_chain(vector_store)
    if not chain:
        return {"error": "Chain initialization failed."}, 500

    # Set sesi sebagai permanen (menggunakan timeout jika diperlukan)
    session.permanent = True

    # Proses chat dan update history, past questions, dan generated responses
    try:
        session['history'], output, source_documents = conversation_chat(user_input, chain, session['history'])
    except Exception as e:
        return {"error": f"An error occurred during chat processing: {str(e)}"}, 500

    # Konversi output ke format HTML menggunakan Markdown
    if source_documents:
        print()
        print("Source documents:", source_documents)
        document_permissions = DocumentPermission.query.filter(DocumentPermission.document_id == source_documents[0].metadata['document_id']).all()
        print("Document permissions:", document_permissions)
        user_permissions = get_allowed_permission_ids()
        print("User permissions:", user_permissions)
        if not any([document_permission.permission_id in user_permissions for document_permission in document_permissions]):
            output = "Anda tidak memiliki izin untuk mendapatkan jawaban dari dokumen yang terkait dengan pertanyaan."
            source_documents = None
        else:
            output = markdown.markdown(output)
    
    else:
        output = markdown.markdown(output)
        source_documents = None

    print()
    print("Output:", output)
    session['generated'].append({
        "message": output,
        "source_documents": [doc.metadata for doc in source_documents] if source_documents else None
    })
    print("Output session:", session['generated'])

    # Kembalikan halaman dengan riwayat pertanyaan dan jawaban yang dihasilkan
    return render_template(
        'guide_bot/index.html', 
        past=session['past_questions'], 
        generated=session['generated']
    )

@guide_bot.route('/guide-bot/reload-vector-db', methods=['GET'])    
def reload_vector_db():
    global embeddings
    
    # permissions = Permission.query.all()
    # for permission in permissions:
    #     documents = Document.query.filter(Document.permission_id == permission.id).all()
        
    #     if len(documents) == 0:
    #         continue
    
    documents = Document.query.all()
    vector_store = load_vector_store(embeddings)
    document_ids = [document.id for document in documents]      
    metadatas = vector_store.get()['metadatas']
    metadatas_document_id = [metadata["document_id"] for metadata in metadatas]        

    for document in documents:
        # Check if document already exists in the vector store
        if document.id in metadatas_document_id:
            print(f"Document {document.id} already exists in the vector store.")
            continue

        # Check if document.file is not None
        if document.dir is None:
            print(f"Document {document.id} has no file dir.")
            continue
        if document.title == 'index':
            print(f"Document {document.id} is an index file.")
            continue
        file_path = os.path.normpath(os.path.join(UPLOAD_FOLDER, document.dir))
        if os.path.exists(file_path):
            all_text = extract_text_from_file(file_path)
        else:
            print(f"File {file_path} not found.")
            continue

        if not all_text.strip():
            print(f"Failed to extract text from document {document.title}")
            continue

        splitted_text = split_documents(all_text)
        
        for text in splitted_text:            
            document_obj = ChatDocument(
                page_content= text,
                metadata = {
                        "id": str(uuid.uuid4()),
                        "title": document.title,
                        "document_id": document.id,                        
                    }
            )
                        
            vector_store.add_documents(
                documents=[document_obj], 
                ids=[document_obj.metadata['id']]
            )
            print(f"Menambahkan dokumen dengan judul {document.title} dan id vector {document_obj.metadata['id']}")

    metadatas = vector_store.get()['metadatas']

    # Delete vector which document_id not in document_ids
    for metadata in metadatas:
        if metadata['document_id'] not in document_ids:
            vector_store.delete([metadata['id']])
            print(f"Menghapus dokumen dengan judul {metadata['title']} dan id {metadata['id']}")

    # return {"message": "Vector store reloaded."}
    return redirect(url_for('guide_bot.manage_documents'))  