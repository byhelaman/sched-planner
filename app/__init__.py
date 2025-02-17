from flask import Flask
from config import Config
import os


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Asegurar que las carpetas existan al iniciar
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["TEMP_FOLDER"], exist_ok=True)

    # Registro de blueprints
    from app.routes import main

    app.register_blueprint(main)

    return app
