"""Notificaciones de cambios de estado (HU-21).

El sistema le envía a NotiSys (simulado en app/integrations/notisys.py) el aviso
para el cliente o para los administradores. Un fallo de NotiSys no frena la
operación que lo originó: queda en el log y en la auditoría de integraciones.
"""

from flask import current_app

from app.integrations import notisys
from app.services import auditoria

DESTINATARIO_ADMINISTRADORES = "administradores"


def notificar_nueva_solicitud(solicitud):
    """Avisa a los administradores que llegó una solicitud nueva."""
    mensaje = (
        f"Nueva solicitud N.º {solicitud.id_solicitud} de {solicitud.cliente.nombre}: "
        f"{solicitud.tipo_modificacion}."
    )
    return _enviar(DESTINATARIO_ADMINISTRADORES, mensaje)


def notificar_resolucion(solicitud):
    """Avisa al cliente que su solicitud fue aprobada o rechazada."""
    mensaje = f"Tu solicitud N.º {solicitud.id_solicitud} fue {solicitud.estado.lower()}."
    return _enviar(solicitud.cliente.email, mensaje)


def notificar_respuesta_reclamo(reclamo):
    """Avisa al cliente que su reclamo cambió de estado."""
    mensaje = f"Tu reclamo N.º {reclamo.id_reclamo} cambió de estado: {reclamo.estado_reclamo}."
    return _enviar(reclamo.cliente.email, mensaje)


def _enviar(destinatario, mensaje):
    respuesta = notisys.enviar(destinatario, mensaje)
    if respuesta["ok"]:
        current_app.logger.info("NotiSys: aviso enviado a %s", destinatario)
    else:
        current_app.logger.warning(
            "NotiSys: no se pudo avisar a %s: %s", destinatario, respuesta["motivo"]
        )
    detalle = f"{destinatario}: {mensaje}" if respuesta["ok"] else f"{destinatario}: {respuesta['motivo']}"
    auditoria.registrar("NotiSys", "enviar_notificacion", respuesta["ok"], detalle)
    return respuesta
