import os


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY", "")
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "storage", "uploads")
    SESSION_FOLDER = os.path.join(BASE_DIR, "storage", "sessions")
    SESSION_EXPIRE_SECONDS = int(os.getenv("SESSION_EXPIRE_SECONDS", 60 * 60))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", 5)) * 1024 * 1024

    for _folder in (UPLOAD_FOLDER, SESSION_FOLDER):
        os.makedirs(_folder, exist_ok=True)

