import pandas as pd
import re


# Utiliza una expresión regular para encontrar todo lo que está entre paréntesis.
def extract_parenthesized_schedule(text):
    matches = re.findall(r"\((.*?)\)", str(text))
    # Retorna una cadena con el contenido extraído, o el texto original si no se encuentran paréntesis.
    return ", ".join(matches) if matches else str(text)


def extract_keyword_from_text(text):
    predefined_keywords = ["CORPORATE", "HUB", "LA MOLINA", "BAW", "KIDS"]
    for keyword in predefined_keywords:
        # Se busca la palabra clave, (sin distinguir mayúsculas/minúsculas)
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
        # Si se encuentra cualquiera de las demás coincidencias (30 o 45), se retorna la palabra clave.
        if re.search(rf"\b{keyword}\b", str(text), re.IGNORECASE):
            return keyword
    return None


def format_time_periods(string):
    return string.replace("a.m.", "AM").replace("p.m.", "PM")


def determine_shift_by_time(start_time):
    try:
        # Convierte la hora a un formato de 24 horas y la formatea a "HH:MM"
        start_time_24h = pd.to_datetime(start_time).strftime("%H:%M")
        return "P. ZUÑIGA" if start_time_24h < "14:00" else "H. GARCIA"
    except:
        return "H. GARCIA"


# Procesa un archivo Excel y extrae información relevante de cada hoja.
def process_excel_file(file_path):
    # Abre el archivo Excel utilizando pandas
    with pd.ExcelFile(file_path) as xls:
        all_schedules = []
        # Itera sobre cada hoja del archivo
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name)

            # Extraer metadatos desde celdas específicas de la hoja
            schedule_date = df.iat[0, 14]
            location = df.iat[0, 21]
            area_name = extract_keyword_from_text(location)
            instructor_name = df.iat[4, 0]
            instructor_code = df.iat[3, 0]

            # Procesar filas a partir de la fila 7 (índice 6) en adelante
            for _, row in df.iloc[6:].iterrows():
                # Se extraen datos específicos de cada fila: tiempo de inicio, fin, grupo y programa
                start_time, end_time, group_name, program_name = (
                    row.iloc[0],
                    row.iloc[3],
                    row.iloc[17],
                    row.iloc[25],
                )

                # Verifica que ninguno de los campos sea nulo o vacío
                if all(
                    pd.notnull(value) and value != ""
                    for value in [start_time, end_time, group_name, program_name]
                ):
                    duration = extract_duration_or_keyword(program_name)
                    # Cuenta cuántas veces aparece el nombre del grupo en las filas procesadas (a partir de la fila 7)
                    unit_count = sum(df.iloc[6:][df.columns[17]] == group_name)
                    shift = determine_shift_by_time(
                        extract_parenthesized_schedule(start_time)
                    )

                    # Si el programa corresponde a "KIDS", se añade la palabra clave al área
                    if extract_keyword_from_text(program_name) == "KIDS":
                        area_name_with_kids = (
                            f"{area_name}/{extract_keyword_from_text(program_name)}"
                        )
                        processed_row = [
                            schedule_date.strftime("%d/%m/%Y"),
                            shift,
                            area_name_with_kids,
                            format_time_periods(
                                extract_parenthesized_schedule(start_time)
                            ),
                            format_time_periods(
                                extract_parenthesized_schedule(end_time)
                            ),
                            instructor_code,
                            instructor_name,
                            group_name,
                            duration,
                            unit_count,
                        ]
                    else:
                        processed_row = [
                            schedule_date.strftime("%d/%m/%Y"),
                            shift,
                            area_name,
                            format_time_periods(
                                extract_parenthesized_schedule(start_time)
                            ),
                            format_time_periods(
                                extract_parenthesized_schedule(end_time)
                            ),
                            instructor_code,
                            instructor_name,
                            group_name,
                            duration,
                            unit_count,
                        ]

                    # Se agrega la fila procesada a la lista global
                    all_schedules.append(processed_row)

        # Retorna la lista completa de horarios procesados
        return all_schedules
