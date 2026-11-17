"""API REST en JSON (RNF-14).

Esta API no usa token CSRF. En su lugar, exigimos Content-Type application/json en
los pedidos que escriben datos: un navegador no puede mandar ese tipo de pedido
desde otro sitio sin permiso explícito (CORS), así que el riesgo queda cubierto.
"""

from flask import Blueprint, abort, jsonify, request, url_for

from app.routes.auth import admin_requerido
from app.services import auditoria as auditoria_service
from app.services import clientes as clientes_service
from app.services import crm as crm_service
from app.services import facturas as facturas_service
from app.services import planes as planes_service
from app.services import reportes as reportes_service
from app.services import servicios as servicios_service
from app.services import solicitudes as solicitudes_service
from app.services import validacion as validacion_service
from app.services.errores import Conflicto, DatosInvalidos, NoEncontrado

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------------------
# HU-07 Gestionar servicios
# ---------------------------------------------------------------------------


@api_bp.get("/servicios")
@admin_requerido
def listar_servicios():
    return jsonify([servicio.a_dict() for servicio in servicios_service.listar_servicios()])


@api_bp.post("/servicios")
@admin_requerido
def crear_servicio():
    servicio = servicios_service.crear_servicio(_leer_json())
    respuesta = jsonify(servicio.a_dict())
    respuesta.status_code = 201
    respuesta.headers["Location"] = url_for("api.obtener_servicio", id_servicio=servicio.id_servicio)
    return respuesta


@api_bp.get("/servicios/<int:id_servicio>")
@admin_requerido
def obtener_servicio(id_servicio):
    return jsonify(servicios_service.obtener_servicio(id_servicio).a_dict())


@api_bp.put("/servicios/<int:id_servicio>")
@admin_requerido
def actualizar_servicio(id_servicio):
    servicio = servicios_service.actualizar_servicio(id_servicio, _leer_json())
    return jsonify(servicio.a_dict())


@api_bp.delete("/servicios/<int:id_servicio>")
@admin_requerido
def eliminar_servicio(id_servicio):
    servicios_service.eliminar_servicio(id_servicio)
    return "", 204


# ---------------------------------------------------------------------------
# HU-06 Gestionar planes
# ---------------------------------------------------------------------------


@api_bp.get("/planes")
@admin_requerido
def listar_planes():
    return jsonify([plan.a_dict() for plan in planes_service.listar_planes()])


@api_bp.post("/planes")
@admin_requerido
def crear_plan():
    plan = planes_service.crear_plan(_leer_json())
    respuesta = jsonify(plan.a_dict())
    respuesta.status_code = 201
    respuesta.headers["Location"] = url_for("api.obtener_plan", id_plan=plan.id_plan)
    return respuesta


@api_bp.get("/planes/<int:id_plan>")
@admin_requerido
def obtener_plan(id_plan):
    return jsonify(planes_service.obtener_plan(id_plan).a_dict())


@api_bp.put("/planes/<int:id_plan>")
@admin_requerido
def actualizar_plan(id_plan):
    plan = planes_service.actualizar_plan(id_plan, _leer_json())
    return jsonify(plan.a_dict())


@api_bp.delete("/planes/<int:id_plan>")
@admin_requerido
def eliminar_plan(id_plan):
    planes_service.eliminar_plan(id_plan)
    return "", 204

# ---------------------------------------------------------------------------
# HU-31 Consultar clientes / HU-04 Detalle de cliente (solo lectura)
# ---------------------------------------------------------------------------


@api_bp.get("/clientes")
@admin_requerido
def listar_clientes():
    return jsonify([cliente.a_dict() for cliente in clientes_service.listar_clientes()])


@api_bp.get("/clientes/<int:id_cliente>")
@admin_requerido
def obtener_cliente(id_cliente):
    cliente = clientes_service.obtener_cliente(id_cliente)
    detalle = cliente.a_dict()
    detalle["plan"] = cliente.plan.a_dict()
    return jsonify(detalle)


@api_bp.get("/clientes/<int:id_cliente>/crmmax")
@admin_requerido
def consultar_cliente_en_crmmax(id_cliente):
    """HU-26: consulta al cliente en CRMMax. Si CRMMax no responde, devuelve 502."""
    cliente = clientes_service.obtener_cliente(id_cliente)
    respuesta = crm_service.consultar_cliente(cliente)
    if not respuesta["ok"]:
        return jsonify(error=respuesta["motivo"]), 502
    return jsonify(respuesta["cliente"])


# ---------------------------------------------------------------------------
# HU-14 Consultar solicitudes (administrador)
# ---------------------------------------------------------------------------


@api_bp.get("/solicitudes")
@admin_requerido
def listar_solicitudes():
    return jsonify([s.a_dict() for s in solicitudes_service.listar_todas()])


@api_bp.get("/solicitudes/<int:id_solicitud>")
@admin_requerido
def obtener_solicitud(id_solicitud):
    return jsonify(solicitudes_service.obtener_solicitud(id_solicitud).a_dict())


@api_bp.put("/solicitudes/<int:id_solicitud>/prioridad")
@admin_requerido
def asignar_prioridad(id_solicitud):
    """HU-13: define la prioridad de una solicitud pendiente."""
    solicitud = solicitudes_service.asignar_prioridad(id_solicitud, _leer_json())
    return jsonify(solicitud.a_dict())


# ---------------------------------------------------------------------------
# HU-32 Facturas, HU-29 Auditoría, HU-27 / HU-28 Métricas
# ---------------------------------------------------------------------------


@api_bp.get("/facturas")
@admin_requerido
def listar_facturas():
    return jsonify([f.a_dict() for f in facturas_service.listar_facturas()])


@api_bp.get("/facturas/<int:id_factura>")
@admin_requerido
def obtener_factura(id_factura):
    return jsonify(facturas_service.obtener_factura(id_factura).a_dict())


@api_bp.get("/auditoria")
@admin_requerido
def listar_auditoria():
    sistema = request.args.get("sistema", "").strip() or None
    return jsonify([r.a_dict() for r in auditoria_service.listar(sistema)])


@api_bp.get("/reportes/metricas")
@admin_requerido
def obtener_metricas():
    return jsonify(reportes_service.metricas_del_dia())


@api_bp.post("/reportes/metricas")
@admin_requerido
def enviar_metricas():
    """HU-27: calcula las métricas del día y las envía a AnalytixPro."""
    metricas, respuesta = reportes_service.generar_metricas_diarias()
    return jsonify(metricas=metricas, analytixpro=respuesta)


# ---------------------------------------------------------------------------
# HU-25 Validar identidad
# ---------------------------------------------------------------------------
@api_bp.post("/validaciones")
@admin_requerido
def validar_identidad():
    return jsonify(validacion_service.validar_identidad(_leer_json()))


# ---------------------------------------------------------------------------
# Utilidades y manejo de errores
# ---------------------------------------------------------------------------


def _leer_json():
    if not request.is_json:
        abort(415)
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise DatosInvalidos({"general": "El cuerpo del pedido debe ser un objeto JSON."})
    return datos


@api_bp.errorhandler(DatosInvalidos)
def _datos_invalidos(error):
    return jsonify(error=error.mensaje, detalles=error.errores), 400


@api_bp.errorhandler(NoEncontrado)
def _no_encontrado(error):
    return jsonify(error=error.mensaje), 404


@api_bp.errorhandler(Conflicto)
def _conflicto(error):
    cuerpo = {"error": error.mensaje}
    if error.campo:
        cuerpo["detalles"] = {error.campo: error.mensaje}
    return jsonify(cuerpo), 409


@api_bp.errorhandler(415)
def _tipo_no_soportado(_error):
    return jsonify(error="El pedido debe enviarse con Content-Type: application/json."), 415
