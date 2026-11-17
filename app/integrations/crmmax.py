"""Simulación de CRMMax (HU-30 / CU Registrar cliente en CRMMax).

CRMMax es un sistema externo que no existe. Por indicación del profesor, su
funcionamiento se simula dentro de nuestro propio código, igual que VeriCheck.
Este módulo es el único que sabe cómo responde CRMMax: si algún día se conectara
uno real, solo habría que cambiar el interior de registrar_cliente().

Regla simulada (suposición del grupo): CRMMax acepta todos los clientes, salvo los
que tienen un email del dominio "crmmax-caido.test". Eso permite mostrar y probar
el caso en que CRMMax no responde.
"""

DOMINIO_CAIDO = "@crmmax-caido.test"
MOTIVO_NO_DISPONIBLE = "CRMMax no está disponible en este momento."


def registrar_cliente(datos):
    """Simula el envío de los datos de un cliente a CRMMax.

    Recibe {"dni", "nombre", "email", "telefono", "plan"} y devuelve
    {"ok": bool, "motivo": str | None}.
    """
    if datos["email"].lower().endswith(DOMINIO_CAIDO):
        return {"ok": False, "motivo": MOTIVO_NO_DISPONIBLE}
    return {"ok": True, "motivo": None}
