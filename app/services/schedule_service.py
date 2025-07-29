import os
from typing import List, Optional

from flask import current_app
from werkzeug.utils import secure_filename

from app.models.schedule_model import Schedule
from app.utils.excel_parser import parse_excel_file
from app.repositories.session_repo import (
    save_data,
    load_data,
    update_data,
    delete_data,
)


def process_uploaded_files(files) -> List[Schedule]:
    """
    Procesa una lista de archivos subidos y devuelve los horarios extraídos.

    Cada archivo se guarda temporalmente en el directorio de subidas
    configurado, se analiza en una lista de objetos :class:`Schedule`
    y luego se elimina. Solo se procesan archivos con extensión ``.xlsx``;
    los demás se ignoran. Las excepciones durante el análisis se propagan
    al llamador.

    Args:
        files: Un iterable de objetos Werkzeug ``FileStorage``.

    Returns:
        Una lista de todos los horarios extraídos de todos los archivos procesados.
    """
    # Recopila las rutas de los archivos válidos. Los archivos se guardan
    # de forma sincrónica para asegurar que existan antes de comenzar el procesamiento.
    file_paths: List[str] = []
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    for file in files:
        filename = file.filename or ""
        if filename.lower().endswith(".xlsx"):
            safe_name = secure_filename(filename)
            file_path = os.path.join(upload_folder, safe_name)
            file.save(file_path)
            file_paths.append(file_path)
    all_schedules: List[Schedule] = []
    # Analiza los archivos guardados de forma concurrente para mejorar el rendimiento
    # cuando se procesan múltiples subidas. Usa un thread pool porque
    # ``parse_excel_file`` realiza E/S y no está limitado por CPU.
    if file_paths:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(parse_excel_file, p): p for p in file_paths}
            for future in as_completed(futures):
                try:
                    schedules = future.result()
                    all_schedules.extend(schedules)
                except Exception as exc:
                    # Registra las excepciones pero continúa procesando otros archivos
                    current_app.logger.error(f"Error parsing {futures[future]}: {exc}")
    # Limpia todos los archivos subidos
    for path in file_paths:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
    return all_schedules


def save_schedules(schedules: List[Schedule], data_id: Optional[str] = None) -> str:
    """
    Persiste una lista de horarios en disco.

    Los horarios se convierten en una lista de diccionarios antes de
    la serialización. Cuando se proporciona ``data_id``, el archivo
    existente con ese identificador se sobrescribirá; de lo contrario,
    se creará uno nuevo y se devolverá un nuevo identificador.

    Args:
        schedules: Una lista de instancias de :class:`Schedule` para guardar.
        data_id: Identificador opcional para los datos de sesión existentes.

    Returns:
        El identificador bajo el cual se guardaron los datos.
    """
    data = [s.to_dict() for s in schedules]
    if data_id:
        update_data(data_id, data)
        return data_id
    return save_data(data)


def load_schedules(data_id: str) -> List[Schedule]:
    """
    Carga horarios previamente persistidos.

    Args:
        data_id: Identificador de la sesión almacenada.

    Returns:
        Una lista de instancias de :class:`Schedule`.

    Raises:
        FileNotFoundError: Si el archivo JSON correspondiente a
            ``data_id`` no existe.
    """
    data = load_data(data_id)
    return [Schedule.from_dict(item) for item in data]


def delete_session_data(data_id: str) -> None:
    """Elimina el archivo de sesión asociado con ``data_id``."""
    delete_data(data_id)


__all__ = [
    "process_uploaded_files",
    "save_schedules",
    "load_schedules",
    "delete_session_data",
]
