import os
from typing import List

import pandas as pd

from app.models.schedule_model import Schedule
from .time_utils import (
    extract_parenthesized_schedule,
    extract_keyword_from_text,
    filter_special_tags,
    extract_duration_or_keyword,
    format_time_periods,
    determine_shift_by_time,
)


def parse_excel_file(file_path: str) -> List[Schedule]:
    """
    Parsea un libro de Excel y extrae una lista de horarios.

    El parser recorre todas las hojas del libro. Se extraen metadatos de celdas específicas
    (ver comentarios en el código) y cada fila a partir de la fila 7 se inspecciona para
    encontrar entradas válidas. Se consideran válidas aquellas filas que contienen ciertos
    campos obligatorios (hora de inicio, hora de fin, grupo y nombre del programa). Las
    duraciones y los nombres de área se infieren usando funciones auxiliares en :mod:`time_utils`.

    Args:
        file_path: Ruta absoluta al archivo de libro de Excel (.xlsx).

    Returns:
        Una lista de instancias de :class:`Schedule` extraídas del archivo.
    """
    schedules: List[Schedule] = []
    with pd.ExcelFile(file_path) as xls:
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name)
            if df.empty:
                continue
            # Extrae metadatos a nivel de hoja. La fecha está almacenada en la fila 0,
            # columna 14; la ubicación en la fila 0, columna 21; el nombre del instructor
            # en la fila 4, columna 0; y el código del instructor en la fila 3, columna 0.
            try:
                schedule_date = df.iat[0, 14]
                location = df.iat[0, 21]
                area_name = extract_keyword_from_text(location) or ""
                instructor_name = df.iat[4, 0]
                instructor_code = df.iat[3, 0]
            except Exception:
                # Omite las hojas que no se ajustan al diseño esperado.
                continue
            # Itera sobre las filas comenzando en el índice 6 (fila 7 en Excel).
            for _, row in df.iloc[6:].iterrows():
                start_time = row.iloc[0]
                end_time = row.iloc[3]
                group_name = row.iloc[17] if len(row) > 17 else None
                raw_block = row.iloc[19] if len(row) > 19 else None

                # Procesar bloque sólo si pasa el filtro
                if pd.notna(raw_block):
                    block_filtered = filter_special_tags(str(raw_block))
                else:
                    block_filtered = None

                program_name = row.iloc[25] if len(row) > 25 else None
                # Omite filas con datos faltantes.
                if not all(
                    pd.notnull(value) and str(value).strip() != ""
                    for value in (start_time, end_time)
                ):
                    continue

                if not (pd.notna(group_name) and str(group_name).strip()):
                    if block_filtered and str(block_filtered).strip():
                        group_name = block_filtered
                    else:
                        continue  # ni grupo ni bloque válidos → saltar fila

                duration = extract_duration_or_keyword(str(program_name)) or ""
                # Cuenta cuántas veces aparece este grupo en el resto de la hoja.
                try:
                    unit_count = int((df.iloc[6:][df.columns[17]] == group_name).sum())
                except Exception:
                    unit_count = 0
                shift = determine_shift_by_time(
                    extract_parenthesized_schedule(str(start_time))
                )
                # Construye el nombre del área; añade "KIDS" para las clases infantiles.
                program_keyword = extract_keyword_from_text(str(program_name))
                area_value = (
                    f"{area_name}/{program_keyword}"
                    if program_keyword == "KIDS" and area_name
                    else area_name
                )
                try:
                    date_str = schedule_date.strftime("%d/%m/%Y")
                except Exception:
                    date_str = str(schedule_date)
                schedule = Schedule(
                    date=date_str,
                    shift=shift,
                    area=area_value,
                    start_time=format_time_periods(
                        extract_parenthesized_schedule(str(start_time))
                    ),
                    end_time=format_time_periods(
                        extract_parenthesized_schedule(str(end_time))
                    ),
                    code=str(instructor_code),
                    instructor=str(instructor_name),
                    group=str(group_name),
                    minutes=str(duration),
                    units=unit_count,
                )
                schedules.append(schedule)
    return schedules


__all__ = ["parse_excel_file"]
