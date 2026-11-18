"""Reglas de negocio para reclamos de clientes (HU-18)."""
from app.extensions import db
from app.models import Reclamo
from app.services.comun import guardar_cambios, texto_obligatorio
from app.services.errores import NoEncontrado, DatosInvalidos

# Importación segura del módulo de NotiSys (evita el ImportError)
try:
    from app.integrations import notisys as notificaciones
except ImportError:
    try:
        from app.integrations import notificaciones
    except ImportError:
        notificaciones = None

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


def listar_todos():
    return Reclamo.query.all()


def obtener_reclamo(id_reclamo):
    """Busca un reclamo por su ID o lanza un error si no existe."""
    reclamo = db.session.get(Reclamo, id_reclamo)
    if not reclamo:
        raise NoEncontrado("El reclamo no existe.")
    return reclamo


def actualizar_reclamo(id_reclamo, datos):
    """Actualiza el estado y la respuesta de un reclamo y notifica al cliente."""
    reclamo = obtener_reclamo(id_reclamo)

    # Se agregan los argumentos 'minimo' y 'maximo' requeridos por texto_obligatorio
    estado = texto_obligatorio(datos, "estado_reclamo", "El estado del reclamo", 1, 50)
    respuesta = texto_obligatorio(datos, "mensaje_respuesta", "La respuesta al cliente", 2, 1000)

    if estado not in [ESTADO_PENDIENTE, ESTADO_RESUELTO, ESTADO_CERRADO]:
        raise DatosInvalidos({"estado_reclamo": "El estado no es válido."})

    reclamo.estado_reclamo = estado
    reclamo.mensaje_respuesta = respuesta
    guardar_cambios()

    # Notifica al cliente mediante NotiSys si está disponible
    if notificaciones and hasattr(notificaciones, "notificar_respuesta_reclamo"):
        try:
            notificaciones.notificar_respuesta_reclamo(reclamo)
        except Exception:
            pass

    return reclamo