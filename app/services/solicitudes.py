"""Reglas de negocio de las solicitudes (HU-08, HU-09, HU-10, HU-11 a HU-14 y HU-16)."""

from datetime import datetime, timezone

from app.extensions import db
from app.models import Plan, Servicio, Solicitud
from app.services import adjuntos as adjuntos_service
from app.services import facturas as facturas_service
from app.services import notificaciones
from app.services.comun import guardar_cambios, texto_obligatorio
from app.services.errores import Conflicto, DatosInvalidos, NoEncontrado

TIPO_CAMBIO_PLAN = "Cambio de plan"

ESTADO_PENDIENTE = "Pendiente"
ESTADO_APROBADA = "Aprobada"
ESTADO_RECHAZADA = "Rechazada"

PRIORIDADES = ("Alta", "Media", "Baja")


def listar_por_cliente(id_cliente):
    consulta = (
        db.select(Solicitud)
        .where(Solicitud.id_cliente == id_cliente)
        .order_by(Solicitud.id_solicitud.desc())
    )
    return db.session.scalars(consulta).all()


def cantidad_pendientes():
    consulta = db.select(db.func.count(Solicitud.id_solicitud)).where(
        Solicitud.estado == "Pendiente"
    )
    return db.session.scalar(consulta) or 0


def crear_cambio_plan(cliente, datos, archivo=None):
    if cliente.plan is None:
        raise DatosInvalidos(
            {"general": "No tenés un plan contratado para solicitar un cambio."}
        )

    id_plan_solicitado = _validar_plan_solicitado(datos, cliente.id_plan)
    motivo = texto_obligatorio(datos, "motivo", "El motivo", 5, 500)
    adjunto = adjuntos_service.guardar(archivo)

    solicitud = Solicitud(
        estado="Pendiente",
        adjunto=adjunto,
        motivo=motivo,
        tipo_modificacion=TIPO_CAMBIO_PLAN,
        id_cliente=cliente.id_cliente,
        id_plan_actual=cliente.id_plan,
        id_plan_solicitado=id_plan_solicitado,
    )
    db.session.add(solicitud)
    guardar_cambios()
    notificaciones.notificar_nueva_solicitud(solicitud)
    return solicitud


def crear_modificacion_servicio(cliente, datos, archivo=None):
    if cliente.plan is None or not cliente.plan.servicios:
        raise DatosInvalidos(
            {"general": "No tenés servicios contratados para solicitar una modificación."}
        )

    servicio = _validar_servicio_contratado(cliente, datos)
    tipo_modificacion = texto_obligatorio(
        datos, "tipo_modificacion", "El tipo de modificación", 3, 50
    )
    motivo = texto_obligatorio(datos, "motivo", "El motivo o detalle", 5, 500)
    adjunto = adjuntos_service.guardar(archivo)

    solicitud = Solicitud(
        estado="Pendiente",
        adjunto=adjunto,
        motivo=motivo,
        tipo_modificacion=tipo_modificacion,
        id_cliente=cliente.id_cliente,
        id_plan_actual=cliente.id_plan,
        id_plan_solicitado=cliente.id_plan,
        id_servicio=servicio.id_servicio,
    )
    db.session.add(solicitud)
    guardar_cambios()
    notificaciones.notificar_nueva_solicitud(solicitud)
    return solicitud


def _validar_plan_solicitado(datos, id_plan_actual):
    valor = datos.get("id_plan_solicitado")
    if not isinstance(valor, str) or not valor.strip().isdecimal():
        raise DatosInvalidos({"id_plan_solicitado": "Seleccioná un plan válido."})

    id_plan = int(valor)
    if id_plan == id_plan_actual:
        raise DatosInvalidos(
            {"id_plan_solicitado": "Seleccioná un plan diferente al actual."}
        )
    if db.session.get(Plan, id_plan) is None:
        raise DatosInvalidos({"id_plan_solicitado": "El plan seleccionado no existe."})
    return id_plan


def _validar_servicio_contratado(cliente, datos):
    valor = datos.get("id_servicio")
    if not isinstance(valor, str) or not valor.strip().isdecimal():
        raise DatosInvalidos({"id_servicio": "Seleccioná un servicio válido."})

    id_servicio = int(valor)
    servicio = db.session.get(Servicio, id_servicio)
    if servicio is None or servicio not in cliente.plan.servicios:
        raise DatosInvalidos(
            {"id_servicio": "El servicio seleccionado no pertenece a tu plan."}
        )
    return servicio


# ---------------------------------------------------------------------------
# HU-14 / HU-11 / HU-12: gestión de solicitudes por el administrador
# ---------------------------------------------------------------------------


def listar_todas():
    """Todas las solicitudes, las más nuevas primero (HU-14)."""
    consulta = db.select(Solicitud).order_by(Solicitud.id_solicitud.desc())
    return db.session.scalars(consulta).all()


def obtener_solicitud(id_solicitud):
    solicitud = db.session.get(Solicitud, id_solicitud)
    if solicitud is None:
        raise NoEncontrado("La solicitud no existe.")
    return solicitud


def aprobar_solicitud(id_solicitud, datos):
    """Aprueba una solicitud pendiente. El comentario es opcional (HU-11)."""
    solicitud = obtener_solicitud(id_solicitud)
    comentario = " ".join(str(datos.get("resultado") or "").split())
    if len(comentario) > 500:
        raise DatosInvalidos({"resultado": "El comentario no puede superar los 500 caracteres."})
    return _resolver(solicitud, ESTADO_APROBADA, comentario or "Solicitud aprobada.")


def rechazar_solicitud(id_solicitud, datos):
    """Rechaza una solicitud pendiente. El motivo es obligatorio (HU-12)."""
    solicitud = obtener_solicitud(id_solicitud)
    motivo = texto_obligatorio(datos, "resultado", "El motivo del rechazo", 5, 500)
    return _resolver(solicitud, ESTADO_RECHAZADA, motivo)


def asignar_prioridad(id_solicitud, datos):
    """Define la prioridad de una solicitud pendiente (HU-13)."""
    solicitud = obtener_solicitud(id_solicitud)
    prioridad = datos.get("prioridad")
    if prioridad not in PRIORIDADES:
        raise DatosInvalidos(
            {"prioridad": "La prioridad debe ser " + ", ".join(PRIORIDADES) + "."}
        )
    if solicitud.estado != ESTADO_PENDIENTE:
        raise Conflicto("Solo se puede cambiar la prioridad de una solicitud pendiente.")
    solicitud.prioridad = prioridad
    guardar_cambios()
    return solicitud


def _resolver(solicitud, estado, resultado):
    # Una solicitud se resuelve una sola vez: así no se pisa una decisión ya tomada.
    if solicitud.estado != ESTADO_PENDIENTE:
        raise Conflicto(f"La solicitud ya fue resuelta (estado: {solicitud.estado}).")

    # HU-15 y HU-16: al aprobar un cambio de plan se pide la factura a PagoNet y, con la
    # factura emitida, el cliente pasa al plan pedido. Si PagoNet falla, no cambia nada.
    # Las solicitudes de servicio llevan id_servicio y no generan factura ni cambian el plan.
    if estado == ESTADO_APROBADA and solicitud.id_servicio is None:
        facturas_service.emitir_por_cambio_de_plan(solicitud)
        solicitud.cliente.id_plan = solicitud.id_plan_solicitado

    solicitud.estado = estado
    solicitud.resultado = resultado
    solicitud.fecha_resolucion = datetime.now(timezone.utc)
    guardar_cambios()
    notificaciones.notificar_resolucion(solicitud)
    return solicitud
