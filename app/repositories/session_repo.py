import json
import os
import uuid
from typing import List, Dict

from flask import current_app


def _get_session_folder() -> str:
    """Devuelve la ruta absoluta al directorio de datos de sesión."""
    return current_app.config["SESSION_FOLDER"]


def save_data(data: List[Dict]) -> str:
    """
    Crea un nuevo archivo de sesión que contiene ``data`` y devuelve su id.

    Se genera un UUID aleatorio para el nombre del archivo. El contenido JSON
    se escribe en la carpeta de sesiones configurada. Si la carpeta no existe,
    se crea.

    Args:
        data: Una lista de diccionarios que representan horarios.

    Returns:
        El identificador de sesión generado.
    """
    file_id = str(uuid.uuid4())
    session_folder = _get_session_folder()
    os.makedirs(session_folder, exist_ok=True)
    file_path = os.path.join(session_folder, f"{file_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return file_id


def load_data(file_id: str) -> List[Dict]:
    """
    Carga la carga útil JSON asociada a ``file_id``.

    Args:
        file_id: El identificador de la sesión.

    Returns:
        El objeto deserializado desde JSON guardado en el archivo.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        json.JSONDecodeError: Si el archivo contiene JSON inválido.
    """
    session_folder = _get_session_folder()
    file_path = os.path.join(session_folder, f"{file_id}.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_data(file_id: str, data: List[Dict]) -> None:
    """Sobrescribe el contenido del archivo de sesión ``file_id`` con ``data``."""
    session_folder = _get_session_folder()
    file_path = os.path.join(session_folder, f"{file_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def delete_data(file_id: str) -> None:
    """Elimina el archivo de sesión ``file_id`` si existe."""
    session_folder = _get_session_folder()
    file_path = os.path.join(session_folder, f"{file_id}.json")
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass


__all__ = ["save_data", "load_data", "update_data", "delete_data"]

#
# Cleanup utilities
#
import time


def remove_expired_sessions(max_age_seconds: int) -> None:
    """
    Elimina archivos de sesión anteriores a ``max_age_seconds``.

    Esta función escanea el directorio de sesiones y borra cualquier
    archivo JSON cuya fecha de modificación supere la edad especificada.

    Args:
        max_age_seconds: El número de segundos tras los cuales una sesión
            se considera expirada.
    """
    session_folder = _get_session_folder()
    now = time.time()
    try:
        for fname in os.listdir(session_folder):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(session_folder, fname)
            try:
                mtime = os.path.getmtime(fpath)
            except FileNotFoundError:
                continue
            if now - mtime > max_age_seconds:
                try:
                    os.remove(fpath)
                except FileNotFoundError:
                    pass
    except FileNotFoundError:
        # El directorio no existe; no hay nada que limpiar.
        pass


__all__.append("remove_expired_sessions")
