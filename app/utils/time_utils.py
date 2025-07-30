import re
import pandas as pd
from typing import Optional


def extract_parenthesized_schedule(text: str) -> str:
    """
    Devuelve el contenido entre paréntesis separado por comas en ``text``.

    Muchas de las celdas de la hoja de cálculo contienen rangos de tiempo
    entre paréntesis. Esta función extrae el contenido de cada conjunto
    de paréntesis y lo concatena con comas. Si no hay paréntesis,
    devuelve el texto original.

    Args:
        text: Contenido bruto de la celda.

    Returns:
        Una cadena con el contenido entre paréntesis separado por comas,
        o el valor original si no se encuentran paréntesis.
    """
    matches = re.findall(r"\((.*?)\)", str(text))
    return ", ".join(matches) if matches else str(text)


def extract_keyword_from_text(text: str) -> Optional[str]:
    """
    Identifica la primera palabra clave de área en una cadena.

    La especificación de AutoSched busca una de un conjunto predefinido
    de subcadenas (``CORPORATE``, ``HUB``, ``LA MOLINA``, ``BAW``, ``KIDS``)
    sin importar mayúsculas o minúsculas. Cuando encuentra una,
    devuelve la palabra clave. Si no encuentra ninguna, devuelve ``None``.

    Args:
        text: La cadena en la que buscar.

    Returns:
        La palabra clave coincidente o ``None``.
    """
    predefined_keywords = ["CORPORATE", "HUB", "LA MOLINA", "BAW", "KIDS"]
    for keyword in predefined_keywords:
        if re.search(rf"\b{keyword}\b", str(text), re.IGNORECASE):
            return keyword
    return None


def filter_special_tags(text: str) -> Optional[str]:
    """
    Elimina cadenas que contengan @corp o @lima2 (ignorando mayúsculas
    y espacios). Si las contiene, devuelve None; en caso contrario, el texto original.
    """
    # Normalizamos el texto: todo en minúsculas y sin espacios
    normalized = re.sub(r"\s+", "", text.lower())

    # Definimos los tags especiales normalizados
    special_tags = [
        "@corp",
        "@lima2",
        "@lcbulevarartigas",  # sin espacios ni mayúsculas
    ]

    # Si cualquier tag aparece en el texto normalizado, filtramos
    if any(tag in normalized for tag in special_tags):
        return None

    return text


def extract_duration_or_keyword(text: str) -> Optional[str]:
    """
    Extrae una duración numérica o palabra clave especial de una cadena.

    Las palabras clave de duración incluyen ``30``, ``45``, ``60``, ``CEIBAL`` y ``KIDS``.
    ``CEIBAL`` y ``KIDS`` se tratan especialmente y ambos se asignan a una
    duración de ``45``. Un programa que contenga ``60`` en su nombre
    en realidad representa 30 minutos porque el curso se divide en dos unidades.

    Args:
        text: El nombre del programa a analizar.

    Returns:
        La duración detectada como cadena, o ``None`` si no hay información
        de duración.
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
    Normaliza los indicadores de hora AM/PM en una cadena.

    Convierte ``a.m.`` y ``p.m.`` en minúsculas a ``AM`` y ``PM``
    en mayúsculas para asegurar un formato consistente al exportar.

    Args:
        string: La cadena de tiempo de entrada.

    Returns:
        Una cadena con ``a.m.`` reemplazado por ``AM`` y ``p.m.`` por ``PM``.
    """
    return string.replace("a.m.", "AM").replace("p.m.", "PM")


def determine_shift_by_time(start_time: str) -> str:
    """
    Determina el turno según la hora de inicio.

    Args:
        start_time: La hora de inicio de la sesión en formato ``HH:MM`` (24h)
            o cualquier formato soportado por ``pandas.to_datetime``.

    Returns:
        El nombre del turno.
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
