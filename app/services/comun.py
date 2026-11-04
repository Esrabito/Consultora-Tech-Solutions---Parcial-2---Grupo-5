"""Validaciones y guardado que comparten los distintos módulos de negocio."""

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.services.errores import Conflicto, DatosInvalidos


def texto_obligatorio(datos, campo, etiqueta, minimo, maximo):
    """Lee un texto obligatorio, le saca los espacios de más y controla el largo.

    `etiqueta` es cómo se nombra el campo en los mensajes, por ejemplo
    "El tipo de servicio" o "El nombre del plan".
    """
    valor = datos.get(campo)
    if valor is not None and not isinstance(valor, str):
        raise DatosInvalidos({campo: f"{etiqueta} debe ser un texto."})

    # "  Plan   Básico " y "Plan Básico" tienen que ser lo mismo.
    texto = " ".join((valor or "").split())

    if not texto:
        raise DatosInvalidos({campo: f"{etiqueta} es obligatorio."})
    if not minimo <= len(texto) <= maximo:
        raise DatosInvalidos({campo: f"{etiqueta} debe tener entre {minimo} y {maximo} caracteres."})
    return texto


def mismo_texto(a, b):
    # Comparamos en Python con casefold() porque lower() de SQLite no maneja tildes
    # ("CONSULTORÍA" vs "consultoría").
    return a.casefold() == b.casefold()


def guardar_cambios():
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise Conflicto("No se pudo guardar: el dato ya existe o está en uso.") from error
