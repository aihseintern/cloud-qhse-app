# app/__init__.py
# import threading
import signal
from flask_cors import CORS
from flask_socketio import SocketIO
import threading
from flask import Flask, current_app, request, session
from base64 import b64encode
from app.extensions import db, migrate, swagger
from app.auth import auth as auth_blueprint
from api.routes import api_routes
from app.routes import app_routes
from flask_login import LoginManager, login_user
from app.models import User
from app.routes import main
# from aios.routes import aios
from flask_mail import Mail

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import os

from utils.detector import DetectorManager
from utils.message import report_selenium_manager, mail_manager, otp_selenium_manager

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
# Initialize Flask-Mail
mail = Mail()

# Initialize Flask-SocketIO
socketio = SocketIO()

# Misal: Manajer detektor yang telah kita buat sebelumnya
detector_manager = DetectorManager(session)
detector_thread = None  # Global variable to store the detector thread

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
DETECTED_OBJECTS_FOLDER = os.path.join(os.getcwd(), 'detected_objects')

def run_detectors(app):
    detector_manager.initialize_detectors(app)

# Tangkap sinyal untuk menghentikan detektor saat server dimatikan
def handle_shutdown_signal(signal, frame):
    global detector_thread  # Use the global variable
    
    print("Shutting down detector manager...")
    detector_manager.stop_all()
    print("Detector manager stopped.")
    if detector_thread is not None:
        print("Waiting for detector thread to join...")
        detector_thread.join()  # Ensure the thread is properly joined
        detector_thread = None
        print("Detector thread joined.")

    print("Shutting down server...")
    os._exit(0)  # Force exit the program

def create_app():
    global detector_thread  # Use the global variable 

    app = Flask(__name__)
    print("App created.")
    app.config.from_object('config.Config')
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    # Konfigurasi direktori upload    
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['DETECTED_OBJECTS_FOLDER'] = DETECTED_OBJECTS_FOLDER
    
    app.secret_key = os.urandom(24)

    # Membuat direktori upload jika belum ada
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Create the directory if it doesn't exist
    if not os.path.exists(DETECTED_OBJECTS_FOLDER):
        os.makedirs(DETECTED_OBJECTS_FOLDER)

    # Define the b64encode filter
    def base64_encode(data):
        return b64encode(data).decode('utf-8')

    # Add the filter to the Jinja2 environment
    app.jinja_env.filters['b64encode'] = base64_encode

    db.init_app(app)
    print("Database initialized.")

    migrate.init_app(app, db)
    print("Migration initialized.")

    swagger.init_app(app)
    print("Swagger initialized.")

    login_manager.init_app(app)
    print("Login manager initialized.")

    # Initialize Flask-SocketIO with the app instance
    socketio.init_app(app)
    print("SocketIO initialized.")
    
    # Initialize Flask-Mail with the app instance
    mail.init_app(app)
    print("Mail initialized.")

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    app.register_blueprint(main)
    app.register_blueprint(auth_blueprint)
    
    for route in app_routes:
        app.register_blueprint(route)
    CORS(
        app, 
        resources={r"/*": {"origins": "*"}},
        origins= ["*"],
        supports_credentials=True,     
    )
    
    
    # mail_manager.init_app(app)
    
    # Selenium
    # report_selenium_manager.initialize_driver()  
    # otp_selenium_manager.initialize_driver()

    # Jalankan thread detektor sebelum memulai Flask
    detector_thread = threading.Thread(target=run_detectors, args=(app,), name="DetectorThread")
    detector_thread.start()

    # Tangkap sinyal SIGINT (Ctrl+C) dan SIGTERM untuk menghentikan detektor saat server dihentikan
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)

    return app
