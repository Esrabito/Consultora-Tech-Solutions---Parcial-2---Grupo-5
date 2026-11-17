"""PagoNet simulado: genera la factura de un cambio de plan (HU-15).

PagoNet es un sistema externo que no existe, así que lo simulamos acá, igual que
VeriCheck y CRMMax. Si algún día hubiera uno real, solo cambia este archivo.
"""

import uuid

# Un email de este dominio hace que PagoNet "no responda". Sirve para mostrar y probar el error.
DOMINIO_CAIDO = "@pagonet-caido.test"
MOTIVO_NO_DISPONIBLE = "PagoNet no está disponible en este momento."


def generar_factura(datos):
    """Recibe {"email", "cliente", "plan", "importe"} y devuelve {"ok", "motivo", "numero"}."""
    if datos["email"].lower().endswith(DOMINIO_CAIDO):
        return {"ok": False, "motivo": MOTIVO_NO_DISPONIBLE, "numero": None}
    return {"ok": True, "motivo": None, "numero": "PN-" + uuid.uuid4().hex[:8].upper()}
