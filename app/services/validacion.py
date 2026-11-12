"""Reglas de negocio de la validación de identidad (HU-25 / CU-1).

Este módulo valida lo que se ingresa, consulta a VeriCheck mediante la simulación
interna de app/integrations/vericheck.py y deja un registro de cada llamada (CU-18,
log básico según la decisión 3 del grupo).
"""

from flask import current_app

from app.integrations import vericheck
from app.services.errores import DatosInvalidos

LARGO_MINIMO_DNI = 7
LARGO_MAXIMO_DNI = 8
LARGO_MINIMO_NOMBRE = 3
LARGO_MAXIMO_NOMBRE = 100

ESTADO_VALIDADO = "VALIDADO"
ESTADO_NO_VALIDADO = "NO_VALIDADO"

MOTIVO_POR_DEFECTO = "VeriCheck no pudo validar los datos personales."


def validar_identidad(datos):
    """Valida los datos personales de un cliente con VeriCheck.

    Devuelve {"dni", "nombre", "estado", "motivo"}: los datos personales más el
    estado de la validación, como pide el CU-1. No guarda nada en la base de datos.
    """
    dni, nombre = _validar_datos(datos)

    # Consulta al cliente simulado interno
    respuesta = vericheck.consultar_identidad(dni, nombre)

    if respuesta["valido"]:
        estado, motivo = ESTADO_VALIDADO, None
    else:
        estado, motivo = ESTADO_NO_VALIDADO, respuesta.get("motivo") or MOTIVO_POR_DEFECTO

    current_app.logger.info("VeriCheck: DNI %s -> %s", _enmascarar(dni), estado)
    return {"dni": dni, "nombre": nombre, "estado": estado, "motivo": motivo}


def _validar_datos(datos):
    """Devuelve (dni, nombre) normalizados o lanza DatosInvalidos con todos los errores."""
    errores = {}
    dni = _validar_dni(datos.get("dni"), errores)
    nombre = _validar_nombre(datos.get("nombre"), errores)
    if errores:
        raise DatosInvalidos(errores)
    return dni, nombre


def _validar_dni(valor, errores):
    if valor is not None and not isinstance(valor, str):
        errores["dni"] = "El DNI debe ser un texto."
        return None

    dni = (valor or "").replace(".", "").replace(" ", "")

    if not dni:
        errores["dni"] = "El DNI es obligatorio."
    elif not dni.isdigit() or not LARGO_MINIMO_DNI <= len(dni) <= LARGO_MAXIMO_DNI:
        errores["dni"] = (
            f"El DNI debe tener entre {LARGO_MINIMO_DNI} y {LARGO_MAXIMO_DNI} números."
        )
    return dni


def _validar_nombre(valor, errores):
    if valor is not None and not isinstance(valor, str):
        errores["nombre"] = "El nombre debe ser un texto."
        return None

    nombre = " ".join((valor or "").split())

    if not nombre:
        errores["nombre"] = "El nombre es obligatorio."
    elif not LARGO_MINIMO_NOMBRE <= len(nombre) <= LARGO_MAXIMO_NOMBRE:
        errores["nombre"] = (
            f"El nombre debe tener entre {LARGO_MINIMO_NOMBRE} "
            f"y {LARGO_MAXIMO_NOMBRE} caracteres."
        )
    return nombre


def _enmascarar(dni):
    """Deja visibles solo los últimos 3 números para no guardar el DNI completo en el log."""
    return "*" * (len(dni) - 3) + dni[-3:]