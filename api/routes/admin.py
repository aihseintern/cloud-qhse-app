from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from flask_login import login_required, current_user
from app import db
from app.models import suMenu, User, Permission, UserPermission
from app.forms import AccessForm, UserApprovalForm, UserPermissionForm
import os
import re
from utils.auth import get_allowed_permission_ids
import logging
from functools import wraps

logging.basicConfig(level=logging.DEBUG)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Custom decorator to require admin privileges
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the user is authenticated and is an admin
        if not current_user.is_admin():
            abort(403)  # Return 403 Forbidden error if not an admin
        return f(*args, **kwargs)
    return decorated_function

# Super user
@admin_bp.route("/user-approval", methods=["GET", "POST"])
@login_required
@admin_required
def user_approval():
    form = UserApprovalForm()
    
    if request.method == "GET":
        applicants = User.query.filter(User.approved.is_(None)).all()
        return render_template("user_approval.html", applicants=applicants, form=form)
    
    elif request.method == "POST":
        if form.validate_on_submit():
            user = User.query.get(form.user_id.data)
            if form.approve.data:
                logging.info("Approved")
                user.approved = True
                flash(f"User {user.name} approved!", "success")
            elif form.reject.data:
                logging.info("Rejected")
                user.approved = False
                flash(f"User {user.name} rejected!", "danger")
            db.session.commit()
            return redirect(url_for("admin.user_approval"))
        else:
            flash("Form validation failed!", "danger")
        return redirect(url_for("admin.user_approval"))

@admin_bp.route("/user-permission", methods=["GET", "POST"])
@admin_bp.route("/user-permission/<int:user_id>", methods=["GET"])
@login_required
@admin_required
def user_permission(user_id=None):
    form = UserPermissionForm()
    if user_id:
        user_permissions = UserPermission.query.filter_by(user_id=user_id).all()
        permission_ids = [up.permission_id for up in user_permissions]
        return jsonify({"permissions": permission_ids})
    
    if request.method == "POST":
        if form.validate_on_submit():
            user_id = form.user_id.data
            selected_permissions = form.permission_id.data
            user = User.query.get(user_id)
            user_permissions = UserPermission.query.join(User).filter(User.id==UserPermission.user_id, UserPermission.user_id==user_id).all()
            for permission_id in selected_permissions:
                if permission_id not in [up.permission_id for up in user_permissions]:
                    new_permission = UserPermission(user_id=user_id, permission_id=permission_id)
                    db.session.add(new_permission)
            for user_permission in user_permissions:
                if user_permission.permission_id not in selected_permissions:
                    db.session.delete(user_permission)
            db.session.commit()
            flash(f"Permissions updated for {user.name}", "success")
        else:
            flash("Form validation failed", "danger")

        return redirect(url_for("admin.user_permission"))

    # For GET requests
    users = User.query.all()
    users.sort(key=lambda x: x.name)
    return render_template("user_permission.html", users=users, form=form)

@admin_bp.route("/", methods=["GET"])
@admin_bp.route("/su", methods=["GET"])
@login_required
@admin_required
def su():
    permissions = Permission.query.all()
    return render_template("su.html", permissions=permissions)

@admin_bp.route("/su/all-cards", methods=["GET"])
@login_required
@admin_required
def all_cards():
    allowed = get_allowed_permission_ids()
    all_cards = suMenu.query.filter(suMenu.permission_id.in_(allowed)).all()

    results = [
        {
            "title": card.title,
            "url": card.url,
            "permission_id": card.permission_id
        }
        for card in all_cards
    ]

    return jsonify(results)

@admin_bp.route("/su/search", methods=["GET"])
@login_required
@admin_required
def search():
    query = request.args.get("query", "")  # Get the query parameter

    if query:
        # Perform a search based on the title
        search_results = suMenu.query.filter(
            suMenu.permission_id.in_(get_allowed_permission_ids()),
            suMenu.title.ilike(f"%{query}%")
            ).all()
    else:
        # If no query, return all results
        search_results = suMenu.query.filter(suMenu.permission_id.in_(get_allowed_permission_ids())).all()

    # Return the results in JSON format
    results = [
        {
            "title": result.title,
            "url": result.url,  # Assuming `url` contains the link for the menu item
            "permission_id": result.permission_id
        }
        for result in search_results
    ]

    return jsonify(results)

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*\t\n]', "_", filename)

UPLOAD_FOLDER = "static/suMenus"

@admin_bp.route("/su/upload", methods=["POST"])
@admin_required
def su_upload():
    title = request.form.get("title")
    file_url = request.form.get("url")
    file = request.files.get("file")
    
    existing_permission_id = request.form.get('existing_permission')
    print(existing_permission_id)
    new_permission = request.form.get('new_permission')
    new_permission_description = request.form.get('new_permission_description')
    
    new_perm_entry = Permission(
            name=new_permission,
            description=new_permission_description
        )
    
    if existing_permission_id and new_permission:
        flash("You cannot select an existing permission and create a new one at the same time.", "error")
        # return redirect(url_for("admin.su"))
        return render_template("su.html")

    if not title:
        flash("Title is required!", "error")
        # return redirect(url_for("admin.su"))
        return render_template("su.html")
    
    if existing_permission_id:
        perm_id = existing_permission_id
    elif new_permission and new_permission_description:
        new_perm_entry = Permission(name=new_permission, description=new_permission_description)
        db.session.add(new_perm_entry)
        db.session.commit()
        perm_id = Permission.query.filter_by(name=new_permission).first().id
    else:
        perm_id = None
    
    if file and file.filename:
        filename = sanitize_filename(file.filename)
        upload_folder = os.path.join(UPLOAD_FOLDER, title)
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        new_menu_entry = suMenu(
            title=title, url=file_url, file=file.read(), path=f"{title}/{filename}",
            permission_id=perm_id
        )
    else:
        new_menu_entry = suMenu(
            title=title,
            permission_id=perm_id
        )
    
    db.session.add(new_menu_entry)
    db.session.commit()

    flash("File uploaded successfully!", "success")
    return redirect(url_for("admin.su"))

# @admin_bp.route("/static/suMenus/<path:filename>")
# def uploaded_file(filename):
#     return send_from_directory("static", filename)


# @admin_bp.route("/su/approval", methods=["GET"])
# def su_approval():
#     # Check if the current user has the 'manager' role
#     if current_user.role.lower() != "manager":
#         return redirect(url_for('admin.su'))
#     # Query users where approval is None or Null
#     applicants = User.query.filter((User.approved.is_(None))).all()
#     return render_template("su_approval.html", applicants=applicants)

# @admin_bp.route("/su/update_approval", methods=["POST", "GET"])
# def su_update_approval():
#     # Get the JSON data from the request
#     data = request.get_json()
#     approved_applicants = data.get("approvedApplicants", [])
#     print(approved_applicants)

#     # Iterate over the approved applicants and update the database
#     for applicant in approved_applicants:
#         if "name" in applicant and "email" in applicant and "role" in applicant:
#             # Query the database for the applicant
#             applicant_record = User.query.filter_by(
#                 name=applicant["name"],
#                 phone_number=applicant["email"],
#                 role=applicant["role"],
#             ).first()

#             if applicant_record:
#                 print(applicant_record)
#                 # Update the record
#                 applicant_record.approved = applicant["approved"]
#                 db.session.commit()
#             else:
#                 # Handle case where applicant is not found, if needed
#                 print(f"Applicant not found: {applicant}")

#     return jsonify(
#         {"status": "success", "message": "Approval data updated successfully"}
#     )

# @admin_bp.route("/su/get_updated_table", methods=['GET'])
# @login_required
# def get_updated_table():
#     # Fetch the updated applicant data from the database
#     applicants = User.query.filter_by(approved=None).all()
#     # Render only the table rows and return as a response
#     return render_template("su_table_rows.html", applicants=applicants)

# # grant access
# @admin_bp.route("/su/grant_access", methods=["GET", "POST"])
# @admin_bp.route("/su/grant_access/<int:user_id>", methods=["GET", "POST"])
# def grant_access(user_id=None):
#     if current_user.role.lower() != "manager":
#         return redirect(url_for('admin.su'))

#     users = User.query.filter((User.role.ilike('%manager%') == False) & (User.approved == True)).all()
#     permissions = {permission.id: permission.name for permission in Permission.query.all()}

#     allowed_permission_ids = get_allowed_permission_ids()  # Get current user's permissions
#     allowed_permission_names = [permissions[perm_id] for perm_id in allowed_permission_ids]

#     form = AccessForm()
    
#     user = User.query.get(user_id) if user_id else None
#     print("WOI INI USER KEMANA?")
#     print(user)
        
#     # Pre-populate the form permissions with the clicked user's current permissions
#     if user and request.method == 'GET':
        
#         # form.permissions.data = [(up.permission_id, up.permission.name) for up in UserPermission.query.join(Permission).filter(Permission.id==UserPermission.permission_id, UserPermission.user_id==user_id).all()]

#         user_permission_ids = [up.permission_id for up in UserPermission.query.filter_by(user_id=user_id).all()]
#         form.permissions.data = user_permission_ids  # Pre-check the clicked user's current permissions
#         print("LU NAPA KOSONG KOCAK")
#         print(form.permissions.data)
#         return render_template("grant_access.html", users=users, user=user, permissions=permissions, allowed_permission_names=allowed_permission_names, form=form, user_permission_ids=user_permission_ids)

#     if request.method == "POST" and form.validate_on_submit():
#         user_id = request.form.get('user_id')
#         user = User.query.get(user_id)

#         if user:
#             selected_permissions = request.form.getlist("permissions")  # Get selected permissions IDs
            
#             # Remove existing permissions that are not selected
#             UserPermission.query.filter(UserPermission.user_id == user_id,
#                                         UserPermission.permission_id.notin_(selected_permissions)).delete(synchronize_session=False)
            
#             # Add new permissions
#             for permission_id in selected_permissions:
#                 if not UserPermission.query.filter_by(user_id=user_id, permission_id=permission_id).first():
#                     new_permission = UserPermission(user_id=user_id, permission_id=permission_id)
#                     db.session.add(new_permission)
            
#             db.session.commit()
#             flash('Permissions updated successfully!', 'success')
#         else:
#             flash('User not found!', 'danger')

#         return redirect(url_for('admin.grant_access'))

#     return render_template("grant_access.html", users=users, user=user, permissions=permissions, allowed_permission_names=allowed_permission_names, form=form)

@admin_bp.route('/set_session', methods=['POST'])
def set_session():
    permission_id = request.form.get('id')    
    if permission_id:
        permission = Permission.query.get(permission_id)
        session['permission_name'] = permission.name
        session['permission_id'] = permission_id
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'error', 'message': 'No ID provided'}), 400

@admin_bp.app_context_processor
def inject_session_permission():
    return dict(session_permission=session.get('permission_id', ''), permission_name=session.get('permission_name', ''))