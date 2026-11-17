"""Sincronización de clientes con CRMMax (HU-30).

Cuando un cliente se registra, sus datos y su plan se envían a CRMMax (simulado en
app/integrations/crmmax.py). Cada intento queda en el log de la aplicación, que es
el registro básico de integraciones que acordó el grupo (decisión 3).

Si CRMMax no responde, el cliente igual queda registrado: no se deshace el alta por
un problema de un sistema externo. El resultado se devuelve para avisarle a quien
registró (suposición del grupo).
"""

from flask import current_app

from app.integrations import crmmax


def registrar_cliente(cliente):
    """Envía el cliente a CRMMax y devuelve {"ok": bool, "motivo": str | None}."""
    datos = {
        "dni": cliente.dni,
        "nombre": cliente.nombre,
        "email": cliente.email,
        "telefono": cliente.telefono,
        "plan": cliente.plan.nombre_plan,
    }
    respuesta = crmmax.registrar_cliente(datos)

    if respuesta["ok"]:
        current_app.logger.info(
            "CRMMax: cliente %s registrado (plan %s)", cliente.id_cliente, datos["plan"]
        )
    else:
        current_app.logger.warning(
            "CRMMax: no se pudo registrar el cliente %s: %s",
            cliente.id_cliente,
            respuesta["motivo"],
        )
    return respuesta
