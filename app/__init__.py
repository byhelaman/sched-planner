import os
from flask import Flask
from config import Config


def create_app(config_class: type = Config) -> Flask:
    """
    Crea y configura una nueva aplicación Flask.

    Args:
        config_class: Una clase de configuración que proporciona atributos
            que Flask entiende. Por defecto es :class:`Config` del módulo
            top-level :mod:`config`.

    Returns:
        La aplicación Flask configurada.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Asegura que existan los directorios de almacenamiento. Esto es redundante
    # con la lógica en :mod:`config`, pero inofensivo y útil cuando la configuración
    # es subclasificada.
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["SESSION_FOLDER"], exist_ok=True)

    # Registra el blueprint principal que contiene todas las rutas. El blueprint
    # vive en ``app/routes.py``. Importarlo aquí evita importaciones circulares
    # que ocurrirían si ``routes.py`` importara la app al nivel de módulo.
    from app.routes import main

    app.register_blueprint(main)

    # Elimina automáticamente archivos de sesión expirados en cada solicitud.
    # Este mecanismo sencillo utiliza la fecha de modificación de los archivos
    # para decidir si un JSON de sesión debe eliminarse. La edad máxima
    # se configura mediante ``SESSION_EXPIRE_SECONDS``.
    from app.repositories.session_repo import remove_expired_sessions

    @app.before_request
    def _cleanup_expired_sessions() -> None:  # type: ignore[override]
        max_age = app.config.get("SESSION_EXPIRE_SECONDS", 60 * 60)
        try:
            remove_expired_sessions(max_age)
        except Exception as exc:
            # Registra y ignora errores de limpieza para que no interrumpan
            # el procesamiento de la solicitud.
            app.logger.error(f"Error cleaning expired sessions: {exc}")

    # Registra un manejador para solicitudes que exceden el ``MAX_CONTENT_LENGTH``
    # configurado. Cuando un usuario sube un archivo demasiado grande, Flask aborta
    # la solicitud con el código 413. Este manejador renderiza la página index
    # con un mensaje de error apropiado.
    from flask import render_template

    @app.errorhandler(413)
    def _too_large(error):  # type: ignore[override]
        message = (
            "The uploaded file is too large. "
            "Please reduce its size or adjust the MAX_UPLOAD_MB variable."
        )
        return render_template("index.html", error=message), 413

    return app


__all__ = ["create_app"]
