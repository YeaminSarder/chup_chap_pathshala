import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    APPROVED_ADMIN_DOMAINS = ['@chupchappathshala.com']
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/static/uploads/covers')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB Limit
