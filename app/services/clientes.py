"""Reglas de negocio para el registro de clientes (HU-01)."""

import re

from app.extensions import db
from app.models import Cliente, Plan
from app.services.comun import guardar_cambios
from app.services.errores import Conflicto, DatosInvalidos


_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def crear_cliente(datos):
    valores = _validar(datos)

    cliente = Cliente(**valores)
    db.session.add(cliente)
    guardar_cambios()
    return cliente


def _validar(datos):
    errores = {}
    valores = {}

    dni = (datos.get("dni") or "").strip()
    if not dni:
        errores["dni"] = "El DNI es obligatorio."
    elif not dni.isdecimal() or not 7 <= len(dni) <= 8:
        errores["dni"] = "El DNI debe tener entre 7 y 8 números."
    else:
        valores["dni"] = dni

    nombre = " ".join((datos.get("nombre") or "").split())
    if not nombre:
        errores["nombre"] = "El nombre es obligatorio."
    elif not 3 <= len(nombre) <= 100:
        errores["nombre"] = "El nombre debe tener entre 3 y 100 caracteres."
    else:
        valores["nombre"] = nombre

    email = (datos.get("email") or "").strip().lower()
    if not email:
        errores["email"] = "El email es obligatorio."
    elif len(email) > 120 or not _EMAIL.fullmatch(email):
        errores["email"] = "El email no tiene un formato válido."
    else:
        valores["email"] = email

    telefono = " ".join((datos.get("telefono") or "").split())
    if not telefono:
        errores["telefono"] = "El teléfono es obligatorio."
    elif len(telefono) > 30:
        errores["telefono"] = "El teléfono no puede superar los 30 caracteres."
    else:
        valores["telefono"] = telefono

    id_plan = datos.get("id_plan")
    if not isinstance(id_plan, str) or not id_plan.strip().isdecimal():
        errores["id_plan"] = "Seleccioná un plan válido."
    else:
        id_plan = int(id_plan)
        if db.session.get(Plan, id_plan) is None:
            errores["id_plan"] = "El plan seleccionado no existe."
        else:
            valores["id_plan"] = id_plan

    if errores:
        raise DatosInvalidos(errores)
    return valores

# ---------------------------------------------------------------------------
# HU-05 / HU-03: identificación del cliente (CU-9, decisión 4)
# ---------------------------------------------------------------------------

# Es el mismo mensaje si falla el DNI, el email o los dos: así no se le revela a
# un tercero si un DNI o un email están registrados.
MENSAJE_IDENTIFICACION = "Los datos ingresados no coinciden con un cliente registrado."


def identificar_cliente(datos):
    """Busca al cliente por DNI y email, sin contraseña (CU-9, decisión 4).

    Devuelve el Cliente. Lanza DatosInvalidos si falta algún dato o si no hay un
    cliente que coincida con los dos.
    """
    dni = _texto(datos.get("dni"))
    email = _texto(datos.get("email")).lower()

    errores = {}
    if not dni:
        errores["dni"] = "El DNI es obligatorio."
    if not email:
        errores["email"] = "El email es obligatorio."
    if errores:
        raise DatosInvalidos(errores)

    cliente = db.session.execute(
        db.select(Cliente).filter_by(dni=dni, email=email)
    ).scalar_one_or_none()
    if cliente is None:
        raise DatosInvalidos({"general": MENSAJE_IDENTIFICACION})
    return cliente


def _texto(valor):
    """Devuelve el texto sin espacios de más, o "" si no es un texto."""
    return valor.strip() if isinstance(valor, str) else ""
