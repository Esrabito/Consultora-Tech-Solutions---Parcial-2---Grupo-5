"""Reglas de negocio para solicitudes de cambio de plan (HU-08)."""

from app.extensions import db
from app.models import Plan, Servicio, Solicitud
from app.services.comun import guardar_cambios, texto_obligatorio
from app.services.errores import DatosInvalidos

TIPO_CAMBIO_PLAN = "Cambio de plan"


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


def crear_cambio_plan(cliente, datos):
    if cliente.plan is None:
        raise DatosInvalidos(
            {"general": "No tenés un plan contratado para solicitar un cambio."}
        )

    id_plan_solicitado = _validar_plan_solicitado(datos, cliente.id_plan)
    motivo = texto_obligatorio(datos, "motivo", "El motivo", 5, 500)

    solicitud = Solicitud(
        estado="Pendiente",
        adjunto=None,
        motivo=motivo,
        tipo_modificacion=TIPO_CAMBIO_PLAN,
        id_cliente=cliente.id_cliente,
        id_plan_actual=cliente.id_plan,
        id_plan_solicitado=id_plan_solicitado,
    )
    db.session.add(solicitud)
    guardar_cambios()
    return solicitud


def crear_modificacion_servicio(cliente, datos):
    if cliente.plan is None or not cliente.plan.servicios:
        raise DatosInvalidos(
            {"general": "No tenés servicios contratados para solicitar una modificación."}
        )

    servicio = _validar_servicio_contratado(cliente, datos)
    tipo_modificacion = texto_obligatorio(
        datos, "tipo_modificacion", "El tipo de modificación", 3, 50
    )
    motivo = texto_obligatorio(datos, "motivo", "El motivo o detalle", 5, 500)

    solicitud = Solicitud(
        estado="Pendiente",
        adjunto=None,
        motivo=motivo,
        tipo_modificacion=tipo_modificacion,
        id_cliente=cliente.id_cliente,
        id_plan_actual=cliente.id_plan,
        id_plan_solicitado=cliente.id_plan,
        id_servicio=servicio.id_servicio,
    )
    db.session.add(solicitud)
    guardar_cambios()
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
