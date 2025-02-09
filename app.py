from flask import Flask, render_template, request, send_file, session, redirect, url_for, abort
import os
import pandas as pd
import re
import uuid
import pickle
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'
app.secret_key = 'tu_clave_secreta_aqui'

# Asegurar que las carpetas existan al iniciar
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

def extract_parenthesized_schedule(text):
    matches = re.findall(r"\((.*?)\)", str(text))
    return ", ".join(matches) if matches else str(text)

def extract_keyword_from_text(text):
    predefined_keywords = ["CORPORATE", "HUB", "LA MOLINA", "BAW", "KIDS"]
    for keyword in predefined_keywords:
        if re.search(rf"\b{keyword}\b", str(text), re.IGNORECASE):
            return keyword
    return None

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

def format_time_periods(string):
    return string.replace("a.m.", "AM").replace("p.m.", "PM")

def determine_shift_by_time(start_time):
    try:
        start_time_24h = pd.to_datetime(start_time).strftime("%H:%M")
        return "P. ZUÑIGA" if start_time_24h < "14:00" else "H. GARCIA"
    except:
        return "H. GARCIA"

def process_excel_file(file_path):
    with pd.ExcelFile(file_path) as xls:
        all_schedules = []
        
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name)
            
            # Extraer metadatos
            schedule_date = df.iat[0, 14]
            location = df.iat[0, 21]
            area_name = extract_keyword_from_text(location)
            instructor_name = df.iat[4, 0]
            instructor_code = df.iat[3, 0]

            # Procesar filas
            for _, row in df.iloc[6:].iterrows():
                start_time, end_time, group_name, program_name = (
                    row.iloc[0], row.iloc[3], row.iloc[17], row.iloc[25]
                )

                if all(pd.notnull(value) and value != "" for value in [start_time, end_time, group_name, program_name]):
                    duration = extract_duration_or_keyword(program_name)
                    unit_count = sum(df.iloc[6:][df.columns[17]] == group_name)
                    shift = determine_shift_by_time(extract_parenthesized_schedule(start_time))

                    # Lógica para KIDS
                    if extract_keyword_from_text(program_name) == "KIDS":
                        area_name_with_kids = f"{area_name}/{extract_keyword_from_text(program_name)}"
                        processed_row = [
                            schedule_date.strftime("%d/%m/%Y"), shift, area_name_with_kids,
                            format_time_periods(extract_parenthesized_schedule(start_time)),
                            format_time_periods(extract_parenthesized_schedule(end_time)),
                            instructor_code, instructor_name, group_name, duration, unit_count
                        ]
                    else:
                        processed_row = [
                            schedule_date.strftime("%d/%m/%Y"), shift, area_name,
                            format_time_periods(extract_parenthesized_schedule(start_time)),
                            format_time_periods(extract_parenthesized_schedule(end_time)),
                            instructor_code, instructor_name, group_name, duration, unit_count
                        ]

                    all_schedules.append(processed_row)

        return all_schedules


@app.route('/download-processed', methods=['POST'])
def download_processed():
    if 'temp_id' not in session:
        session.clear()
        return redirect(url_for('index'))
    
    temp_id = session.get('temp_id')
    temp_file = os.path.join(app.config['TEMP_FOLDER'], f"{temp_id}.pkl")
    
    if not os.path.exists(temp_file):
        session.clear()
        return redirect(url_for('index'))
    
    try:
        with open(temp_file, 'rb') as f:
            all_schedules = pickle.load(f)
    except Exception as e:
        abort(500, f"Error al cargar los datos: {str(e)}")
    
    # Obtener índices a eliminar
    deleted_indices = request.form.get('selected_rows', '')
    deleted_indices = list(map(int, deleted_indices.split(','))) if deleted_indices else []
    
    # Filtrar datos
    filtered_data = [row for idx, row in enumerate(all_schedules) if idx not in deleted_indices]
    
    # Generar Excel
    final_df = pd.DataFrame(filtered_data, columns=[
        "Date", "Shift", "Area", "Start Time", "End Time", 
        "Code", "Instructor", "Group", "Minutes", "Units"
    ])
    
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], "schedule.xlsx")
    final_df.to_excel(output_path, index=False)
    
    # Enviar y eliminar archivo generado
    try:
        response = send_file(
            output_path,
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            download_name="schedule.xlsx"
        )
        
        # Eliminar archivo temporal y de salida después de enviar
        def remove_files():
            try:
                os.remove(temp_file)
                os.remove(output_path)
            except Exception as e:
                app.logger.error(f"Error limpiando archivos: {str(e)}")

        response.call_on_close(remove_files)
        
    except Exception as e:
        app.logger.error(f"Error al enviar archivo: {str(e)}")
        abort(500)
    
    # Limpiar toda la sesión
    session.clear()
    session.modified = True
    
    return response

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('files')
        all_schedules = []
        uploaded_files = []
        
        try:
            # Procesar archivos
            for file in files:
                if file.filename.endswith('.xlsx'):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    uploaded_files.append(file_path)
                    all_schedules.extend(process_excel_file(file_path))
            
            # Eliminar archivos subidos
            for file_path in uploaded_files:
                for _ in range(3):
                    try:
                        os.remove(file_path)
                        break
                    except PermissionError:
                        time.sleep(0.5)
            
            # Guardar en temporal si hay datos
            if all_schedules:
                temp_id = str(uuid.uuid4())
                temp_file = os.path.join(app.config['TEMP_FOLDER'], f"{temp_id}.pkl")
                with open(temp_file, 'wb') as f:
                    pickle.dump(all_schedules, f)
                
                session['temp_id'] = temp_id
                session.modified = True
                return render_template('index.html', schedules=all_schedules)
        
        except Exception as e:
            # Limpiar archivos residuales
            for file_path in uploaded_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            return render_template('index.html', error=str(e))
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)