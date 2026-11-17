"""Reglas de negocio para reclamos de clientes (HU-18)."""
from app.extensions import db
from app.models import Reclamo
from app.services.comun import guardar_cambios, texto_obligatorio

ESTADO_PENDIENTE = "Pendiente"
ESTADO_RESUELTO = "Resuelto"
ESTADO_CERRADO = "Cerrado"


def listar_por_cliente(id_cliente):
    """Devuelve los reclamos de un cliente, los más recientes primero."""
    consulta = (
        db.select(Reclamo)
        .where(Reclamo.id_cliente == id_cliente)
        .order_by(Reclamo.id_reclamo.desc())
    )
    return db.session.scalars(consulta).all()


def crear_reclamo(cliente, datos):
    """Registra un reclamo nuevo en estado Pendiente para el cliente."""
    mensaje = texto_obligatorio(
        datos, "mensaje_reclamo", "El detalle del reclamo", 5, 500
    )

    reclamo = Reclamo(
        id_cliente=cliente.id_cliente,
        mensaje_reclamo=mensaje,
        estado_reclamo=ESTADO_PENDIENTE,
    )
    db.session.add(reclamo)
    guardar_cambios()
    return reclamo