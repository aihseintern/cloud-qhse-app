from flask_login import current_user
from app.models import UserPermission, Permission

def get_allowed_permission_ids():
    if not current_user.is_authenticated:
        # Handle the case where the user is not authenticated
        return []

    user_permissions = UserPermission.query.filter_by(user_id=current_user.id).all()
    allowed_permission_ids =  [user_permission.permission_id for user_permission in user_permissions]
    print("allowed_permission_ids", allowed_permission_ids)
    return allowed_permission_ids
