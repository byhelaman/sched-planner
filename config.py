import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'g&9kYT1GBvhP@K9H')
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    TEMP_FOLDER = os.path.join(os.getcwd(), 'temp')