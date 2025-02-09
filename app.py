from flask import Flask, render_template, request, send_file, session, abort
import os
import pandas as pd
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'tu_clave_secreta_aqui'

# Extrae el horario de un texto dentro de paréntesis
def extract_parenthesized_schedule(text):
    matches = re.findall(r"\((.*?)\)", str(text))
    return ", ".join(matches) if matches else str(text)

# Extrae una palabra clave específica de un texto según una lista predefinida
def extract_keyword_from_text(text):
    predefined_keywords = ["CORPORATE", "HUB", "LA MOLINA", "BAW", "KIDS"]
    for keyword in predefined_keywords:
        if re.search(rf"\b{keyword}\b", str(text), re.IGNORECASE):
            return keyword
    return None

# Extrae la duración o una palabra clave relacionada del texto
def extract_duration_or_keyword(text):
    duration_keywords = ["30", "45", "60", "CEIBAL", "KIDS"]
    for keyword in duration_keywords:
        if keyword in ["CEIBAL", "KIDS"]:
            return "45"
        if keyword == "60" and re.search(rf"\b{keyword}\b", str(text), re.IGNORECASE):
            return "30"
        if re.search(rf"\b{keyword}\b", str(text), re.IGNORECASE):
            return keyword
    return None

# Reemplaza 'a.m.' y 'p.m.' con formatos 'AM' y 'PM'
def format_time_periods(string):
    return string.replace("a.m.", "AM").replace("p.m.", "PM")

# Determina si el turno es matutino o vespertino según la hora de inicio
def determine_shift_by_time(start_time):
    start_time_24h = pd.to_datetime(start_time).strftime("%H:%M")
    return "P. ZUÑIGA" if start_time_24h < "14:00" else "H. GARCIA"

# Procesa un archivo de Excel y extrae datos relevantes
def process_excel_file(file_path):
    xls = pd.ExcelFile(file_path)
    all_schedules = []

    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name)

        schedule_date = df.iat[0, 14]
        location = df.iat[0, 21]
        area_name = extract_keyword_from_text(location)
        instructor_name = df.iat[4, 0]
        instructor_code = df.iat[3, 0]

        processed_data = []

        for _, row in df.iloc[6:].iterrows():
            start_time, end_time, group_name, program_name = (
                row.iloc[0], row.iloc[3], row.iloc[17], row.iloc[25]
            )

            if all(pd.notnull(value) and value != "" for value in [start_time, end_time, group_name, program_name]):
                duration = extract_duration_or_keyword(program_name)
                unit_count = sum(df.iloc[6:][df.columns[17]] == group_name)
                shift = determine_shift_by_time(extract_parenthesized_schedule(start_time))

                if extract_keyword_from_text(program_name) == "KIDS":
                    area_name_with_kids = f"{area_name}/{extract_keyword_from_text(program_name)}"
                    processed_data.append([
                        schedule_date.strftime("%d/%m/%Y"), shift, area_name_with_kids,
                        format_time_periods(extract_parenthesized_schedule(start_time)),
                        format_time_periods(extract_parenthesized_schedule(end_time)),
                        instructor_code, instructor_name, group_name, duration, unit_count
                    ])
                else:
                    processed_data.append([
                        schedule_date.strftime("%d/%m/%Y"), shift, area_name,
                        format_time_periods(extract_parenthesized_schedule(start_time)),
                        format_time_periods(extract_parenthesized_schedule(end_time)),
                        instructor_code, instructor_name, group_name, duration, unit_count
                    ])

        all_schedules.extend(processed_data)

    return all_schedules


@app.route('/download-processed', methods=['POST'])
def download_processed():
    if 'original_schedules' not in session:
        abort(400, "No data available for processing")
    
    deleted_indices = request.form.get('selected_rows', '')
    deleted_indices = list(map(int, deleted_indices.split(','))) if deleted_indices else []

    all_schedules = session['original_schedules']
    
    # Mantener solo las filas que no fueron eliminadas en el preview
    filtered_data = [row for idx, row in enumerate(all_schedules) if idx not in deleted_indices]

    final_schedule_df = pd.DataFrame(filtered_data, columns=[
        "Date", "Shift", "Area", "Start Time", "End Time", "Code",
        "Instructor", "Group", "Minutes", "Units"
    ])
    
    output_file_path = os.path.join(app.config['UPLOAD_FOLDER'], "schedule.xlsx")
    final_schedule_df.to_excel(output_file_path, index=False)
    
    return send_file(output_file_path, as_attachment=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    schedules = None

    if request.method == 'POST':
        files = request.files.getlist('files')
        all_schedules = []

        for file in files:
            if file and file.filename.endswith('.xlsx'):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                all_schedules.extend(process_excel_file(file_path))

        if all_schedules:
            session['original_schedules'] = all_schedules  # Guardar en session

            schedules = all_schedules  # Pasar los datos a la plantilla

    return render_template('index.html', schedules=schedules)


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)