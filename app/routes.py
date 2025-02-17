import pandas as pd
import os
import time

from flask import (
    Blueprint,
    render_template,
    request,
    send_file,
    session,
    redirect,
    url_for,
    abort,
    current_app,
)

from werkzeug.utils import secure_filename
from .utils.process import process_excel_file
from .utils.temporary import (
    save_temporary_data,
    load_temporary_data,
    update_temporary_data,
    delete_temporary_data,
)

main = Blueprint("main", __name__)


@main.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Obtiene la lista de archivos subidos con la clave 'files'
        files = request.files.getlist("files")
        all_schedules = []  # Lista para almacenar todos los horarios procesados

        try:
            # Itera sobre cada archivo subido
            for file in files:
                # Solo procesa archivos con extensión ".xlsx"
                if file.filename.endswith(".xlsx"):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(
                        current_app.config["UPLOAD_FOLDER"], filename
                    )
                    file.save(file_path)

                    # Procesa el archivo Excel y extiende la lista de horarios con los datos extraídos
                    all_schedules.extend(process_excel_file(file_path))
                    os.remove(file_path)

            # Se guardan los datos procesados en un archivo temporal y se almacena el ID en la sesión
            if all_schedules:
                data_id = session.get("data_id")
                if data_id:
                    # Actualiza los datos existentes
                    update_temporary_data(data_id, all_schedules)
                else:
                    # No existe datos previos, se crea uno nuevo
                    data_id = save_temporary_data(all_schedules)
                    session["data_id"] = data_id

                session.modified = True
                all_schedules = load_temporary_data(data_id)
                return redirect(url_for("main.index"))

        except Exception as e:
            return render_template("index.html", error=str(e))

    # GET, Se obtienen los datos desde el archivo temporal usando el ID almacenado en la sesión
    data_id = session.get("data_id")
    if data_id:
        try:
            all_schedules = load_temporary_data(data_id)
        except FileNotFoundError:
            all_schedules = []
            session.clear()
    else:
        all_schedules = []
    return render_template("index.html", schedules=all_schedules)


# Nueva ruta para eliminar filas y actualizar la sesión
@main.route("/delete-rows", methods=["POST"])
def delete_rows():
    if "data_id" not in session:
        return redirect(url_for("main.index"))

    data_id = session.get("data_id")
    all_schedules = load_temporary_data(data_id)

    # Se obtienen los índices de las filas a eliminar enviados desde el formulario
    deleted_indices = request.form.get("selected_rows", "")
    deleted_indices = (
        list(map(int, deleted_indices.split(","))) if deleted_indices else []
    )

    # Se filtran los datos eliminando las filas cuyos índices están en la lista de eliminados
    filtered_data = [
        row for idx, row in enumerate(all_schedules) if idx not in deleted_indices
    ]

    # Actualiza la sesión con los datos filtrados
    update_temporary_data(data_id, filtered_data)
    return redirect(url_for("main.index"))


# Ruta para la descarga del archivo Excel procesado.
@main.route("/download-processed", methods=["POST"])
def download_processed():
    if "data_id" not in session:
        session.clear()
        return redirect(url_for("main.index"))

    data_id = session.get("data_id")
    all_schedules = load_temporary_data(data_id)

    # Se genera un DataFrame con los datos filtrados, asignando nombres de columnas específicos
    final_df = pd.DataFrame(
        all_schedules,
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

    # Se define la ruta de salida para el archivo Excel generado
    output_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "schedule.xlsx")
    final_df.to_excel(output_path, index=False)

    try:
        # Se envía el archivo Excel generado como respuesta para descarga
        response = send_file(
            output_path,
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            download_name="schedule.xlsx",
        )

    except Exception as e:
        current_app.logger.error(f"Error al enviar archivo: {str(e)}")
        abort(500)

    return response


@main.route("/destroy-session", methods=["POST"])
def destroy_session():
    # Si existe un data_id en la sesión, se elimina el archivo temporal asociado.
    data_id = session.get("data_id")
    if data_id:
        try:
            delete_temporary_data(data_id)
        except Exception as e:
            current_app.logger.error(f"Error al eliminar datos temporales: {str(e)}")

    # Limpia los archivos en la carpeta UPLOAD_FOLDER
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    try:
        for file in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        current_app.logger.error(f"Error al limpiar archivos en uploads: {str(e)}")

    # Se limpia la sesión
    session.clear()
    return redirect(url_for("main.index"))
