import pandas as pd
import os
import uuid
import pickle
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

from io import BytesIO
from werkzeug.utils import secure_filename
from .utils.functions import process_excel_file

main = Blueprint("main", __name__)


@main.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Obtiene la lista de archivos subidos con la clave 'files'
        files = request.files.getlist("files")
        all_schedules = []  # Lista para almacenar todos los horarios procesados
        uploaded_files = []  # Lista para almacenar las rutas de archivos subidos

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
                    uploaded_files.append(file_path)
                    # Procesa el archivo Excel y extiende la lista de horarios con los datos extraídos
                    all_schedules.extend(process_excel_file(file_path))

            # Después de procesar, se intenta eliminar los archivos subidos para liberar espacio
            for file_path in uploaded_files:
                for _ in range(3):
                    try:
                        os.remove(file_path)
                        break
                    except PermissionError:
                        time.sleep(0.5)

            # Si se han extraído horarios, se guardan temporalmente utilizando pickle
            if all_schedules:
                # Genera un identificador único para la sesión temporal
                temp_id = str(uuid.uuid4())
                temp_file = os.path.join(
                    current_app.config["TEMP_FOLDER"], f"{temp_id}.pkl"
                )

                # Guarda la lista de horarios en un archivo pickle
                with open(temp_file, "wb") as f:
                    pickle.dump(all_schedules, f)

                # Se guarda el identificador temporal en la sesión del usuario
                session["temp_id"] = temp_id
                session.modified = True

                # Se renderiza la plantilla pasando los horarios procesados para su visualización
                return render_template("index.html", schedules=all_schedules)

        except Exception as e:
            # En caso de error, se eliminan los archivos subidos que aún existan para limpiar recursos
            for file_path in uploaded_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            return render_template("index.html", error=str(e))

    # Para solicitudes GET, simplemente renderiza la plantilla sin datos procesados.
    return render_template("index.html")


# Ruta para la descarga del archivo Excel procesado.
@main.route("/download-processed", methods=["POST"])
def download_processed():
    if "temp_id" not in session:
        session.clear()
        return redirect(url_for("main.index"))

    # Verifica que exista un identificador temporal en la sesión
    temp_id = session.get("temp_id")
    temp_file = os.path.join(current_app.config["TEMP_FOLDER"], f"{temp_id}.pkl")

    # Si el archivo temporal no existe, se redirige a la página principal y se limpia la sesión
    if not os.path.exists(temp_file):
        session.clear()
        return redirect(url_for("main.index"))

    try:
        # Se carga la lista de horarios procesados desde el archivo pickle
        with open(temp_file, "rb") as f:
            all_schedules = pickle.load(f)
    except Exception as e:
        abort(500, f"Error al cargar los datos: {str(e)}")

    # Se obtienen los índices de las filas que se desean eliminar, enviados desde el formulario
    deleted_indices = request.form.get("selected_rows", "")
    deleted_indices = (
        list(map(int, deleted_indices.split(","))) if deleted_indices else []
    )

    # Se filtran los datos eliminando las filas cuyos índices están en la lista de eliminados
    filtered_data = [
        row for idx, row in enumerate(all_schedules) if idx not in deleted_indices
    ]

    # Se genera un DataFrame con los datos filtrados, asignando nombres de columnas específicos
    final_df = pd.DataFrame(
        filtered_data,
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

        # Función que se ejecutará al cerrar la respuesta para limpiar archivos temporales
        def remove_files():
            try:
                os.remove(temp_file)
                os.remove(output_path)
            except Exception as e:
                current_app.logger.error(f"Error limpiando archivos: {str(e)}")

        response.call_on_close(remove_files)

    except Exception as e:
        current_app.logger.error(f"Error al enviar archivo: {str(e)}")
        abort(500)

    # Finalmente, se limpia la sesión y se marca como modificada.
    session.clear()
    session.modified = True

    return response
