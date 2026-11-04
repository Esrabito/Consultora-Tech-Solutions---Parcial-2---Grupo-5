"""Reglas de negocio de los servicios (HU-07 / CU-15 Gestionar servicios)."""

from app.extensions import db
from app.models import Servicio
from app.services.comun import guardar_cambios, mismo_texto, texto_obligatorio
from app.services.errores import Conflicto, NoEncontrado

LARGO_MINIMO_TIPO = 3
LARGO_MAXIMO_TIPO = 100


def listar_servicios():
    consulta = db.select(Servicio).order_by(Servicio.tipo_servicio)
    return db.session.scalars(consulta).all()


def obtener_servicio(id_servicio):
    servicio = db.session.get(Servicio, id_servicio)
    if servicio is None:
        raise NoEncontrado("El servicio no existe.")
    return servicio


def crear_servicio(datos):
    tipo = _validar_tipo(datos)
    _verificar_tipo_disponible(tipo)

    servicio = Servicio(tipo_servicio=tipo)
    db.session.add(servicio)
    guardar_cambios()
    return servicio


def actualizar_servicio(id_servicio, datos):
    servicio = obtener_servicio(id_servicio)
    tipo = _validar_tipo(datos)
    _verificar_tipo_disponible(tipo, excluir_id=servicio.id_servicio)

    servicio.tipo_servicio = tipo
    guardar_cambios()
    return servicio


def eliminar_servicio(id_servicio):
    servicio = obtener_servicio(id_servicio)

    # CU-15 E2: un servicio incluido en algún plan no se puede eliminar.
    if servicio.planes:
        nombres = ", ".join(plan.nombre_plan for plan in servicio.planes)
        raise Conflicto(
            f"No se puede eliminar el servicio porque está incluido en estos planes: {nombres}. "
            "Primero quitalo de esos planes."
        )

    db.session.delete(servicio)
    guardar_cambios()


def _validar_tipo(datos):
    return texto_obligatorio(
        datos, "tipo_servicio", "El tipo de servicio", LARGO_MINIMO_TIPO, LARGO_MAXIMO_TIPO
    )


def _verificar_tipo_disponible(tipo, excluir_id=None):
    # El catálogo es chico, así que recorrerlo entero no pesa.
    for servicio in listar_servicios():
        if servicio.id_servicio != excluir_id and mismo_texto(servicio.tipo_servicio, tipo):
            raise Conflicto("Ya existe un servicio con ese tipo.", campo="tipo_servicio")
