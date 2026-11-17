"""NotiSys simulado: envía notificaciones a clientes y administradores (HU-21).

NotiSys no existe; lo simulamos como VeriCheck y CRMMax. Un destinatario de este
dominio hace que el envío falle, para mostrar el caso de error.
"""

DOMINIO_CAIDO = "@notisys-caido.test"
MOTIVO_NO_DISPONIBLE = "NotiSys no está disponible en este momento."


def enviar(destinatario, mensaje):
    """Devuelve {"ok": bool, "motivo": str | None}."""
    if destinatario.lower().endswith(DOMINIO_CAIDO):
        return {"ok": False, "motivo": MOTIVO_NO_DISPONIBLE}
    return {"ok": True, "motivo": None}
