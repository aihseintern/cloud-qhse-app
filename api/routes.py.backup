# import os
# from flask import Blueprint, abort, render_template, redirect, send_file, url_for, flash, request, session, jsonify
# from langchain_chroma import Chroma
# from langchain_huggingface import HuggingFaceEmbeddings
# from guide_bot import conversation_chat, create_conversational_chain, load_vector_store, save_uploaded_file, load_saved_files, split_documents
# from guide_bot.models import Document
# from guide_bot.forms import DocumentFileForm, DocumentFolderForm
# from werkzeug.utils import secure_filename
# from app import db
# from PyPDF2 import PdfReader
# import docx2txt
# from pptx import Presentation
# import pandas
# from langchain_core.documents import Document as ChatDocument

# api = Blueprint('api', __name__, url_prefix='/api')

# # Initialize variables
# history = []
# generated = ["Selamat datang di GuideBot! Tanyakan sesuatu pada saya 😊️"]
# past = []

# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'})

# @api.route('/guide-bot/chat', methods=['POST'])
# def chat():
#     global history, generated, past

#     if request.method == 'POST':
#         user_input = request.form.get('user_input', '')        
#         vector_store = load_vector_store(embeddings)
#         print("Vector store loaded")
#         if vector_store:
#             print("Vector store is not empty")
#             chain = create_conversational_chain(vector_store)
#             print("Conversational chain created")
#             print("History:", history)
#             output, source_documents = conversation_chat(user_input, chain, history)
#             print("Output:", output)
#             print("Conversation completed")
#             past.append(user_input)
#             generated.append({
#                 "message": output,
#                 "source_documents": source_documents
#             })
#         else:
#             flash('⚠️ No documents uploaded by admin yet.', 'warning')

#         # Return JSON response
#         return jsonify({
#             "user_input": user_input,
#             "response": {
#                 "message": output,
#                 "source_documents": [
#                     {
#                         "id": doc.metadata['id'],
#                         "title": doc.metadata['title'],
#                         "snippet": doc.page_content[:200]  # Example: first 200 characters
#                     }
#                     for doc in source_documents
#                 ] if source_documents else []
#             },
#             "history": past
#         }), 200

#     return 400
 
# @api.route('/guide-bot/upload', methods=['POST'])
# def manage_documents():
#     file_form = DocumentFileForm()
#     folder_form = DocumentFolderForm()
#     # Proses penambahan dokumen
#     if file_form.validate_on_submit() or folder_form.validate_on_submit():
#         files = request.files.getlist('files')
#         for file in files:
#             filename = secure_filename(file.filename)
#             # Simpan dokumen dalam database
#             new_document = Document(title=filename, file=file.read())
#             db.session.add(new_document)
#             db.session.commit()

#             # Save the file to disk with its document ID
#             # save_dir = 'data'
#             # if not os.path.exists(save_dir):
#             #     os.makedirs(save_dir)
#             # file_path = os.path.join(save_dir, f"{filename}")
#             # with open(file_path, 'wb') as f:
#             #     f.write(new_document.file)

#         return 200
    
#     return 400

# @api.route('/guide-bot/reload-vector-db', methods=['GET'])
# def reload_vector_db():
#     vector_store = Chroma(
#         collection_name="SPIL",
#         embedding_function=embeddings or HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'}), 
#         persist_directory="vector_store"
#     )
#     # Load all documents from the SQL database
#     documents = Document.query.all()
#     document_ids = [str(document.id) for document in documents]    
#     vector_store_ids = vector_store.get()['ids']    
#     print("Documents:", document_ids)    
#     print("Vector store IDs:", vector_store_ids)

#     # Prepare documents for vector store
#     for document in documents:
#         vector_store_ids = vector_store.get()['ids']
#         print("Vector store IDs:", vector_store_ids)
#         # Check if document already exists in the vector store
#         if str(document.id) in vector_store_ids:
#             continue           

#         file_path = os.path.join('data', secure_filename(document.title))

#         # Save the file to disk with its document ID
#         save_dir = 'data'
#         if not os.path.exists(save_dir):
#             os.makedirs(save_dir)
#         with open(file_path, 'wb') as f:
#             f.write(document.file)
        
#         # Extract text based on file type
#         all_text = ""
#         if file_path.endswith('.pdf'):
#             pdf_reader = PdfReader(file_path)
#             for page in pdf_reader.pages:
#                 text = page.extract_text()
#                 if text:
#                     all_text += text
#         elif file_path.endswith('.docx'):
#             all_text = docx2txt.process(file_path)        
#         elif file_path.endswith('.ods') or file_path.endswith('.xls') or file_path.endswith('.xlsx'):
#             df = pandas.read_excel(file_path)
#             all_text = df.to_string()
#         elif file_path.endswith('.pptx'):
#             presentation = Presentation(file_path)
#             for slide in presentation.slides:
#                 for shape in slide.shapes:
#                     if hasattr(shape, "text"):
#                         all_text += shape.text        
#         elif file_path.endswith('.txt'):
#             with open(file_path, 'r', encoding='utf-8') as file:
#                 all_text = file.read()
        
#         if not all_text.strip():
#             print("Failed to extract text from the document.")
#             flash("Failed to extract text from the document.")
#             continue

#         document_obj = ChatDocument(
#              page_content= all_text,
#              metadata = {
#                     "title": document.title,
#                     "file_path": file_path,
#                     "id": document.id
#                 }
#         )
        
#         if len(vector_store_ids) == 0:
#             print("Vector store is empty")
#             vector_store = Chroma.from_documents(
#                 embedding=embeddings,
#                 collection_name="SPIL",
#                 documents=[document_obj], 
#                 persist_directory="vector_store",
#                 ids=[str(document.id)])
#             print("Vector store created")
#         else:
#             print("Vector store is not empty")
#             vector_store.add_documents(
#                 documents=[document_obj], 
#                 ids=[str(document.id)]
#             )
#             print("Document with ID", document.id, "added to vector store")

#         # Delete data
#         if os.path.exists(file_path):
#             os.remove(file_path)
#             print("Deleted file", file_path)

#     for vector_id in vector_store_ids:
#         if vector_id not in document_ids:
#             vector_store.delete(ids=[vector_id])
#             print(f"Deleted vector with id {vector_id}")

#     return 200