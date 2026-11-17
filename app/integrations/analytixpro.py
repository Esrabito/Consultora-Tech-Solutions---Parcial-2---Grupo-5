"""AnalytixPro simulado: recibe las métricas diarias para los dashboards (HU-27).

AnalytixPro no existe; lo simulamos como VeriCheck y CRMMax. Acepta las métricas
y confirma cuántas recibió.
"""


def enviar_metricas(metricas):
    """Devuelve {"ok": True, "recibidas": cantidad de métricas}."""
    return {"ok": True, "recibidas": len(metricas)}
