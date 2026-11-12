"""Reglas de negocio de los planes (HU-06 / CU-14 Gestionar planes)."""

import re
from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models import Plan, Servicio
from app.services.comun import guardar_cambios, mismo_texto, texto_obligatorio
from app.services.errores import Conflicto, DatosInvalidos, NoEncontrado

LARGO_MINIMO_NOMBRE = 3
LARGO_MAXIMO_NOMBRE = 100
# Numeric(10, 2) admite hasta 8 cifras enteras.
VALOR_MAXIMO = Decimal("99999999.99")
# "15.000" o "1.250.000": puntos agrupando de a 3 cifras, sin coma decimal.
SEPARADOR_DE_MILES = re.compile(r"\d{1,3}(\.\d{3})+")


def listar_planes():
    consulta = db.select(Plan).order_by(Plan.nombre_plan)
    return db.session.scalars(consulta).all()


def obtener_plan(id_plan):
    plan = db.session.get(Plan, id_plan)
    if plan is None:
        raise NoEncontrado("El plan no existe.")
    return plan


def crear_plan(datos):
    valores = _validar(datos)
    _verificar_nombre_disponible(valores["nombre_plan"])

    plan = Plan(**valores)
    db.session.add(plan)
    guardar_cambios()
    return plan


def actualizar_plan(id_plan, datos):
    plan = obtener_plan(id_plan)
    valores = _validar(datos)
    _verificar_nombre_disponible(valores["nombre_plan"], excluir_id=plan.id_plan)

    plan.nombre_plan = valores["nombre_plan"]
    plan.valor_plan = valores["valor_plan"]
    plan.servicios = valores["servicios"]
    guardar_cambios()
    return plan


def eliminar_plan(id_plan):
    plan = obtener_plan(id_plan)

    # CU-14 E2: un plan con clientes asignados no se puede eliminar.
    cantidad = len(plan.clientes)
    if cantidad:
        clientes = "1 cliente" if cantidad == 1 else f"{cantidad} clientes"
        raise Conflicto(
            f"No se puede eliminar el plan porque tiene {clientes} asignados. "
            "Primero hay que cambiarles el plan."
        )

    db.session.delete(plan)
    guardar_cambios()


# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------


def _validar(datos):
    """Valida todos los campos juntos, así el formulario muestra todos los errores de una vez."""
    validaciones = {
        "nombre_plan": _validar_nombre,
        "valor_plan": _validar_valor,
        "servicios": _validar_servicios,
    }
    valores, errores = {}, {}
    for campo, validar in validaciones.items():
        try:
            valores[campo] = validar(datos)
        except DatosInvalidos as error:
            errores.update(error.errores)

    if errores:
        raise DatosInvalidos(errores)
    return valores


def _validar_nombre(datos):
    return texto_obligatorio(
        datos, "nombre_plan", "El nombre del plan", LARGO_MINIMO_NOMBRE, LARGO_MAXIMO_NOMBRE
    )


def _validar_valor(datos):
    valor = datos.get("valor_plan")
    invalido = DatosInvalidos({"valor_plan": "El valor del plan debe ser un número."})

    # bool es un tipo de int en Python, así que lo descartamos primero.
    if isinstance(valor, bool):
        raise invalido
    if isinstance(valor, (int, float)):
        texto = str(valor)
    elif isinstance(valor, str):
        texto = valor.strip()
        # Aceptamos el formato de acá: "15.000,50", "15000,50" o "15.000".
        if "," in texto or SEPARADOR_DE_MILES.fullmatch(texto):
            texto = texto.replace(".", "").replace(",", ".")
    elif valor is None:
        texto = ""
    else:
        raise invalido

    if not texto:
        raise DatosInvalidos({"valor_plan": "El valor del plan es obligatorio."})

    try:
        numero = Decimal(texto)
    except InvalidOperation:
        raise invalido from None

    if not numero.is_finite():
        raise invalido
    if numero <= 0:
        raise DatosInvalidos({"valor_plan": "El valor del plan debe ser mayor que 0."})
    if numero > VALOR_MAXIMO:
        raise DatosInvalidos({"valor_plan": "El valor del plan no puede superar $ 99.999.999,99."})
    if numero != numero.quantize(Decimal("0.01")):
        raise DatosInvalidos({"valor_plan": "El valor del plan puede tener como máximo 2 decimales."})

    return numero.quantize(Decimal("0.01"))


def _validar_servicios(datos):
    ids = datos.get("servicios")
    if ids is None:
        ids = []
    if not isinstance(ids, list):
        raise DatosInvalidos({"servicios": "Los servicios deben enviarse como una lista de números."})

    elegidos = []
    for valor in ids:
        id_servicio = _a_entero(valor)
        if id_servicio is None:
            raise DatosInvalidos({"servicios": "Los servicios deben enviarse como una lista de números."})
        if id_servicio not in elegidos:
            elegidos.append(id_servicio)

    # Diccionario de Datos: un plan incluye al menos un servicio (decisión 8).
    if not elegidos:
        raise DatosInvalidos({"servicios": "Elegí al menos un servicio para el plan."})

    consulta = db.select(Servicio).where(Servicio.id_servicio.in_(elegidos))
    servicios = db.session.scalars(consulta).all()
    if len(servicios) != len(elegidos):
        raise DatosInvalidos({"servicios": "Alguno de los servicios elegidos no existe."})
    return servicios


def _a_entero(valor):
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str) and valor.strip().isdecimal():
        return int(valor)
    return None


def _verificar_nombre_disponible(nombre, excluir_id=None):
    for plan in listar_planes():
        if plan.id_plan != excluir_id and mismo_texto(plan.nombre_plan, nombre):
            raise Conflicto("Ya existe un plan con ese nombre.", campo="nombre_plan")
