"""Sincronización de clientes con CRMMax (HU-30 y HU-26).

Cuando un cliente se registra, sus datos y su plan se envían a CRMMax (simulado en
app/integrations/crmmax.py). Cada intento queda en el log de la aplicación y en la
auditoría de integraciones (HU-29).

Si CRMMax no responde, el cliente igual queda registrado: no se deshace el alta por
un problema de un sistema externo. El resultado se devuelve para avisarle a quien
registró (suposición del grupo).
"""

from flask import current_app

from app.integrations import crmmax
from app.services import auditoria


def registrar_cliente(cliente):
    """Envía el cliente a CRMMax y devuelve {"ok": bool, "motivo": str | None}."""
    datos = _datos_del_cliente(cliente)
    respuesta = crmmax.registrar_cliente(datos)

    if respuesta["ok"]:
        current_app.logger.info(
            "CRMMax: cliente %s registrado (plan %s)", cliente.id_cliente, datos["plan"]
        )
        detalle = f"Cliente {cliente.id_cliente} registrado (plan {datos['plan']})."
    else:
        current_app.logger.warning(
            "CRMMax: no se pudo registrar el cliente %s: %s",
            cliente.id_cliente,
            respuesta["motivo"],
        )
        detalle = f"Cliente {cliente.id_cliente}: {respuesta['motivo']}"

    auditoria.registrar("CRMMax", "registrar_cliente", respuesta["ok"], detalle)
    return respuesta


def consultar_cliente(cliente):
    """Consulta al cliente en CRMMax (HU-26). Devuelve {"ok", "motivo", "cliente"}."""
    respuesta = crmmax.consultar_cliente(_datos_del_cliente(cliente))

    if respuesta["ok"]:
        detalle = f"Cliente {cliente.id_cliente} consultado."
    else:
        detalle = f"Cliente {cliente.id_cliente}: {respuesta['motivo']}"
    current_app.logger.info("CRMMax: consulta del cliente %s -> %s", cliente.id_cliente, respuesta["ok"])
    auditoria.registrar("CRMMax", "consultar_cliente", respuesta["ok"], detalle)
    return respuesta


def _datos_del_cliente(cliente):
    return {
        "dni": cliente.dni,
        "nombre": cliente.nombre,
        "email": cliente.email,
        "telefono": cliente.telefono,
        "plan": cliente.plan.nombre_plan,
    }
