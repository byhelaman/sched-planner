import os
import uuid
import json
from flask import current_app


# Funciones para manejar el almacenamiento temporal de datos en archivos JSON
def save_temporary_data(data):
    file_id = str(uuid.uuid4())
    temp_folder = current_app.config["TEMP_FOLDER"]
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    file_path = os.path.join(temp_folder, f"{file_id}.json")
    with open(file_path, "w") as f:
        json.dump(data, f)

    return file_id


def load_temporary_data(file_id):
    temp_folder = current_app.config["TEMP_FOLDER"]

    file_path = os.path.join(temp_folder, f"{file_id}.json")
    with open(file_path, "r") as f:
        data = json.load(f)

    return data


def update_temporary_data(file_id, data):
    temp_folder = current_app.config["TEMP_FOLDER"]

    file_path = os.path.join(temp_folder, f"{file_id}.json")
    with open(file_path, "w") as f:
        json.dump(data, f)


def delete_temporary_data(file_id):
    temp_folder = current_app.config["TEMP_FOLDER"]
    file_path = os.path.join(temp_folder, f"{file_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
