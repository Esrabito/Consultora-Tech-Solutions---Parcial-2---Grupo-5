"""Reglas de negocio de los servicios (HU-07 / CU-15 Gestionar servicios)."""

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Servicio
from app.services.errores import Conflicto, DatosInvalidos, NoEncontrado

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
    _guardar()
    return servicio


def actualizar_servicio(id_servicio, datos):
    servicio = obtener_servicio(id_servicio)
    tipo = _validar_tipo(datos)
    _verificar_tipo_disponible(tipo, excluir_id=servicio.id_servicio)

    servicio.tipo_servicio = tipo
    _guardar()
    return servicio


def eliminar_servicio(id_servicio):
    servicio = obtener_servicio(id_servicio)
    db.session.delete(servicio)
    _guardar()


def _validar_tipo(datos):
    valor = datos.get("tipo_servicio")
    if valor is not None and not isinstance(valor, str):
        raise DatosInvalidos({"tipo_servicio": "El tipo de servicio debe ser un texto."})

    # Sacamos espacios de más para que "  Legal   " y "Legal" sean lo mismo.
    tipo = " ".join((valor or "").split())

    if not tipo:
        raise DatosInvalidos({"tipo_servicio": "El tipo de servicio es obligatorio."})
    if not LARGO_MINIMO_TIPO <= len(tipo) <= LARGO_MAXIMO_TIPO:
        raise DatosInvalidos(
            {
                "tipo_servicio": (
                    f"El tipo de servicio debe tener entre {LARGO_MINIMO_TIPO} "
                    f"y {LARGO_MAXIMO_TIPO} caracteres."
                )
            }
        )
    return tipo


def _verificar_tipo_disponible(tipo, excluir_id=None):
    # Comparamos en Python con casefold() porque lower() de SQLite no maneja tildes
    # ("CONSULTORÍA" vs "consultoría"). El catálogo es chico, así que no pesa.
    buscado = tipo.casefold()
    for servicio in listar_servicios():
        if servicio.id_servicio != excluir_id and servicio.tipo_servicio.casefold() == buscado:
            raise Conflicto("Ya existe un servicio con ese tipo.", campo="tipo_servicio")


def _guardar():
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise Conflicto("No se pudo guardar: el dato ya existe o está en uso.") from error
