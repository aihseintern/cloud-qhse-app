from api.routes.cctv import cctv_bp
from api.routes.contact import contact_bp
from api.routes.detector import detector_bp
from api.routes.document import document_bp
from api.routes.message import message_bp
from api.routes.notification import notification_bp
from api.routes.report import report_bp
from api.routes.weight import weight_bp
from api.routes.admin import admin_bp

api_routes = [
    cctv_bp,
    contact_bp,
    detector_bp,
    document_bp,
    message_bp,
    notification_bp,
    report_bp,
    weight_bp,
    admin_bp,

]