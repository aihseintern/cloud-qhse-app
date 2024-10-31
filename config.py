import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_TRACK_MODIFICATIONS = False    

    # Setup default sql alchemy bind from local database
    SQLALCHEMY_BINDS = {
        'default': os.getenv('DATABASE_URL2', 'postgresql://user:password@localhost:5432/local_database'),
        'DATABASE_URL1': os.getenv('DATABASE_URL1', 'postgresql://user:password@localhost:5432/depo_database'),
        'DATABASE_URL2': os.getenv('DATABASE_URL2', 'postgresql://user:password@localhost:5432/local_database')
    }

    # Database URIs can be stored here if needed for use in the switch_database function
    DATABASE_URL1 = os.getenv('DATABASE_URL1', 'postgresql://user:password@localhost:5432/depo_database')
    DATABASE_URL2 = os.getenv('DATABASE_URL2', 'postgresql://user:password@localhost:5432/local_database')

    # Konfigurasi API WhatsApp
    WHATSAPP_API_URL = os.environ.get('WHATSAPP_API_URL') or 'https://api.whatsapp.com/send'
    WHATSAPP_API_KEY = os.environ.get('WHATSAPP_API_KEY') or 'your-whatsapp-api-key'
    
    MAIL_SERVER = 'smtp.gmail.com'  # Use Gmail's SMTP server
    MAIL_PORT = 587  # Gmail uses port 587 for TLS
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')  # Your email address
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')  # App-specific password if using Gmail
