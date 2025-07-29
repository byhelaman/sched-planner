from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class Schedule:
    """
    Representa una única entrada de horario.

    Los atributos reflejan las columnas en el archivo Excel exportado y el
    orden en que los datos se muestran en la interfaz de usuario. Todos los
    valores son cadenas excepto :attr:`units`, que almacena la cantidad de
    ocurrencias de un grupo específico dentro de la hoja de origen.
    """

    date: str
    shift: str
    area: str
    start_time: str
    end_time: str
    code: str
    instructor: str
    group: str
    minutes: str
    units: int

    def to_dict(self) -> Dict[str, object]:
        """
        Convierte la instancia de Schedule en un diccionario serializable.

        Devuelve:
            Una representación en ``dict`` adecuada para la codificación JSON.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Schedule":
        """
        Crea un :class:`Schedule` a partir de un diccionario.

        Args:
            data: Un mapeo con claves que coinciden con los nombres de los campos del dataclass.

        Devuelve:
            Una nueva instancia de :class:`Schedule`.
        """
        return cls(**data)


__all__ = ["Schedule"]
