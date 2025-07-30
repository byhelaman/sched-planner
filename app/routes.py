import os
import json
from typing import List

import pandas as pd
from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    request,
    Response,
    send_file,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from app.services.schedule_service import (
    process_uploaded_files,
    load_schedules,
    save_schedules,
    delete_session_data,
)
from app.models.schedule_model import Schedule

main = Blueprint("main", __name__)


def _serialize_schedules(schedules: List[Schedule]) -> List[List[object]]:
    """
    Convierte una lista de objetos :class:`Schedule` en una lista de listas.

    La plantilla del front-end espera una lista plana de valores para cada
    horario. Esta función centraliza esa lógica de conversión.

    Args:
        schedules: Una lista de instancias de :class:`Schedule`.

    Returns:
        Una lista de listas, cada lista interna contiene los atributos
        del horario en el orden esperado por la plantilla.
    """
    return [
        [
            s.date,
            s.shift,
            s.area,
            s.start_time,
            s.end_time,
            s.code,
            s.instructor,
            s.group,
            s.minutes,
            s.units,
        ]
        for s in schedules
    ]


@main.route("/", methods=["GET", "POST"])
def index():
    """
    Renderiza la página principal o procesa archivos subidos.

    En ``POST``, el usuario ha subido uno o varios archivos Excel.
    Los archivos se procesan y los horarios extraídos se guardan en
    la sesión. Al realizar subidas sucesivas en la misma sesión,
    los datos se fusionan. Tras el procesamiento, se redirige a
    ``GET`` el índice para mostrar los resultados.

    En ``GET``, se recuperan los horarios existentes de la sesión
    y se muestran en la plantilla. Si no hay horarios, se muestra
    una página vacía.
    """
    if request.method == "POST":
        # Recupera los archivos subidos. ``request.files.getlist`` devuelve
        # una lista vacía si no se han seleccionado archivos.
        files = request.files.getlist("files")
        if files:
            try:
                new_schedules = process_uploaded_files(files)
                if new_schedules:
                    data_id = session.get("data_id")
                    if data_id:
                        # Añade a los horarios existentes en lugar de sobrescribir.
                        existing = load_schedules(data_id)
                        existing.extend(new_schedules)
                        save_schedules(existing, data_id=data_id)
                    else:
                        data_id = save_schedules(new_schedules)
                        session["data_id"] = data_id
                    session.modified = True
                # Siempre redirige tras el procesamiento para evitar reenvíos.
                return redirect(url_for("main.index"))
            except Exception as e:
                # Registra el error y muestra la página con mensaje de error.
                current_app.logger.error(f"Error processing upload: {e}")
                return render_template("index.html", error=str(e))
        # No se proporcionaron archivos; recarga la página.
        return redirect(url_for("main.index"))

    # GET: recupera los horarios guardados en la sesión.
    data_id = session.get("data_id")
    if data_id:
        try:
            schedules = load_schedules(data_id)
        except FileNotFoundError:
            # Datos de sesión faltantes en disco; limpia la sesión y empieza de nuevo.
            current_app.logger.warning(
                "Session data file missing; clearing session for data_id=%s", data_id
            )
            schedules = []
            session.clear()
    else:
        schedules = []
    # Convierte a lista de listas para la plantilla.
    display_data = _serialize_schedules(schedules)
    return render_template("index.html", schedules=display_data)


@main.route("/delete-rows", methods=["POST"])
def delete_rows():
    """
    Gestiona la eliminación de filas seleccionadas de los horarios almacenados.

    El cuerpo del POST contiene ``selected_rows``, una lista separada
    por comas de índices basados en cero a eliminar. Tras la eliminación,
    los horarios actualizados se guardan y el usuario es redirigido
    de nuevo al índice.
    """
    data_id = session.get("data_id")
    if not data_id:
        return redirect(url_for("main.index"))
    try:
        schedules = load_schedules(data_id)
    except FileNotFoundError:
        # Nada que eliminar.
        session.clear()
        return redirect(url_for("main.index"))
    # Parsea los índices separados por comas; filtra cadenas vacías.
    indices_str = request.form.get("selected_rows", "")
    indices = [int(i) for i in indices_str.split(",") if i]
    # Filtra los horarios excluyendo los índices seleccionados.
    filtered = [s for idx, s in enumerate(schedules) if idx not in indices]
    save_schedules(filtered, data_id=data_id)
    return redirect(url_for("main.index"))


@main.route("/download-processed", methods=["POST"])
def download_processed():
    """
    Genera y envía un archivo Excel con los horarios actuales.

    Los horarios se cargan de la sesión y se convierten en un DataFrame
    de pandas con nombres de columna legibles. El archivo resultante
    se guarda en el directorio de subidas y se envía al cliente
    usando la función :func:`send_file` de Flask.
    """
    data_id = session.get("data_id")
    if not data_id:
        session.clear()
        return redirect(url_for("main.index"))
    try:
        schedules = load_schedules(data_id)
    except FileNotFoundError:
        session.clear()
        return redirect(url_for("main.index"))
    # Construye el DataFrame a partir de los horarios.
    df = pd.DataFrame(
        _serialize_schedules(schedules),
        columns=[
            "Date",
            "Shift",
            "Area",
            "Start Time",
            "End Time",
            "Code",
            "Instructor",
            "Group",
            "Minutes",
            "Units",
        ],
    )
    # Guarda en un archivo en el directorio de subidas; reutiliza el mismo nombre
    # en cada descarga. Los archivos existentes se sobrescriben.
    output_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "schedule.xlsx")
    df.to_excel(output_path, index=False)
    try:
        return send_file(
            output_path,
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            download_name="schedule.xlsx",
        )
    except Exception as e:
        current_app.logger.error(f"Error sending file: {e}")
        abort(500)


@main.route("/destroy-session", methods=["POST"])
def destroy_session():
    """
    Elimina todos los datos de sesión y archivos subidos.

    Borra el archivo JSON de la sesión, limpia el directorio de subidas
    y limpia la sesión de Flask. Luego redirige de vuelta al índice.
    """
    data_id = session.get("data_id")
    if data_id:
        try:
            delete_session_data(data_id)
        except Exception as e:
            current_app.logger.error(f"Error deleting session data: {e}")
    # Limpia el directorio de archivos subidos.
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    try:
        for fname in os.listdir(upload_folder):
            fpath = os.path.join(upload_folder, fname)
            if os.path.isfile(fpath):
                os.remove(fpath)
    except Exception as e:
        current_app.logger.error(f"Error cleaning uploads: {e}")
    # Limpia las cookies de sesión.
    session.clear()
    return redirect(url_for("main.index"))


@main.route("/copy", methods=["GET"])
def copy():
    """
    Devuelve una representación TSV de los horarios actuales para copiar.

    Los horarios se cargan y se escriben en una cadena tipo CSV con
    separadores de tabulación, sin encabezado ni índice. El resultado
    se envuelve en una respuesta text/csv para que los navegadores
    lo traten como descargable si es necesario, pero el JS del lado
    del cliente puede leerlo como texto plano y copiarlo al portapapeles.
    """
    data_id = session.get("data_id")
    if not data_id:
        abort(404)
    try:
        schedules = load_schedules(data_id)
    except FileNotFoundError:
        abort(404)
    df = pd.DataFrame(_serialize_schedules(schedules))
    tsv = df.to_csv(header=False, index=False, sep="\t")
    return Response(
        tsv,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=schedule.csv"},
    )


__all__ = ["main"]
