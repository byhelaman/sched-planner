import re
import pandas as pd
from typing import Optional


def extract_parenthesized_schedule(text: str) -> str:
    """
    Extrae y concatena el contenido entre paréntesis de una cadena.

    Muchas celdas del archivo contienen rangos horarios dentro de paréntesis.
    Esta función recupera todos los contenidos entre paréntesis y los une
    con comas. Si no se encuentran paréntesis, devuelve el texto original.

    Args:
        text: Cadena de entrada, típicamente el contenido de una celda.

    Returns:
        Cadena con los contenidos entre paréntesis separados por comas,
        o el texto original si no se encuentra ninguno.
    """

    matches = re.findall(r"\((.*?)\)", str(text))
    return ", ".join(matches) if matches else str(text)


def extract_keyword_from_text(text: str) -> Optional[str]:
    """
    Busca y devuelve la primera palabra clave de área detectada en una cadena.

    Se compara contra un conjunto predefinido de palabras clave:
    "CORPORATE", "HUB", "LA MOLINA", "BAW", "KIDS", ignorando mayúsculas.

    Args:
        text: Cadena en la que buscar la palabra clave.

    Returns:
        La palabra clave detectada o None si no se encuentra ninguna.
    """

    predefined_keywords = ["CORPORATE", "HUB", "LA MOLINA", "BAW", "KIDS"]
    for keyword in predefined_keywords:
        if re.search(rf"\b{keyword}\b", str(text), re.IGNORECASE):
            return keyword
    return None


def filter_special_tags(text: str) -> Optional[str]:
    """
    Filtra etiquetas especiales predefinidas como "@corp", "@lima 2", etc.

    Normaliza el texto eliminando espacios y convirtiendo a minúsculas,
    y lo compara contra una lista de variantes también normalizadas.
    Si hay coincidencia exacta, devuelve None. En caso contrario, conserva el texto.

    Args:
        text: Cadena a evaluar.

    Returns:
        None si el texto coincide con un tag especial; el texto original en caso contrario.
    """
    
    # Normalizamos el texto: minúsculas y sin espacios
    normalized_text = re.sub(r"\s+", "", text.lower())

    # Lista de variantes de tags a filtrar, normalizadas de antemano
    special_tags = {
        re.sub(r"\s+", "", variant).lower()
        for group in [
            "@Corp",
            "@Lima 2 | lima2 | @Lima Corporate",
            "@LC Bulevar Artigas",
            "@Argentina",
        ]
        for variant in group.split("|")
    }

    # Si hay coincidencia exacta con alguna variante, se filtra
    if normalized_text in special_tags:
        return None

    return text


def extract_duration_or_keyword(text: str) -> Optional[str]:
    """
    Extrae una duración o palabra clave de duración de una cadena.

    Busca los valores "30", "45", "60", "CEIBAL" y "KIDS" en la cadena:
    - "CEIBAL" y "KIDS" se consideran como 45 minutos.
    - Si se encuentra "60", se interpreta como 30 minutos (por división del curso).
    - Si se encuentra "30" o "45", se devuelve tal cual.

    Args:
        text: Nombre del programa o cadena descriptiva.

    Returns:
        Duración como cadena ("30" o "45"), o None si no se detecta ninguna.
    """

    duration_keywords = ["30", "45", "60", "CEIBAL", "KIDS"]
    for keyword in duration_keywords:
        if keyword in ["CEIBAL", "KIDS"]:
            return "45"
        if keyword == "60" and re.search(rf"\b{keyword}\b", str(text), re.IGNORECASE):
            # Programa de 60 minutos cuenta como 30
            return "30"
        if re.search(rf"\b{keyword}\b", str(text), re.IGNORECASE):
            return keyword
    return None


def format_time_periods(string: str) -> str:
    """
    Normaliza los indicadores AM/PM en una cadena de tiempo.
    
    Reemplaza "a.m." por "AM" y "p.m." por "PM" para mantener consistencia.

    Args:
        string: Cadena que contiene información horaria.

    Returns:
        Cadena con formato AM/PM estandarizado.
    """

    return string.replace("a.m.", "AM").replace("p.m.", "PM")


def determine_shift_by_time(start_time: str) -> str:
    """
    Determina el turno según la hora de inicio.

    Args:
        start_time: Hora de inicio (ej. "13:30", "2:00 PM", etc.).

    Returns:
        Nombre del turno correspondiente.
    """

    try:
        start_time_24h = pd.to_datetime(start_time).strftime("%H:%M")
        return "P. ZUÑIGA" if start_time_24h < "14:00" else "H. GARCIA"
    except Exception:
        return "H. GARCIA"


__all__ = [
    "extract_parenthesized_schedule",
    "extract_keyword_from_text",
    "filter_special_tags",
    "extract_duration_or_keyword",
    "format_time_periods",
    "determine_shift_by_time",
]
