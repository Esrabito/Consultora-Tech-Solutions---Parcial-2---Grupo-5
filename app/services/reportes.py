"""Métricas diarias y reportes operativos (HU-27 y HU-28).

Las métricas se calculan sobre nuestra base. Generar las métricas diarias las envía
además a AnalytixPro (simulado en app/integrations/analytixpro.py), que las usa para
sus dashboards. El "día" se toma en UTC, igual que las fechas que guardamos.
"""

from datetime import datetime, timezone

from app.extensions import db
from app.integrations import analytixpro
from app.models import Cliente, Factura, Reclamo, Solicitud
from app.services import auditoria

ESTADO_RECLAMO_ABIERTO = "Pendiente"


def metricas_del_dia():
    """Devuelve un diccionario con las métricas de hoy (HU-28)."""
    inicio_del_dia = datetime.now(timezone.utc).replace(
        tzinfo=None, hour=0, minute=0, second=0, microsecond=0
    )

    def contar(*condiciones, modelo):
        consulta = db.select(db.func.count()).select_from(modelo).where(*condiciones)
        return db.session.scalar(consulta) or 0

    importe_facturado = db.session.scalar(db.select(db.func.sum(Factura.importe))) or 0

    return {
        "fecha": inicio_del_dia.date().isoformat(),
        "total_clientes": contar(modelo=Cliente),
        "nuevos_registros": contar(Cliente.fecha_registro >= inicio_del_dia, modelo=Cliente),
        "solicitudes_generadas": contar(
            Solicitud.fecha_creacion >= inicio_del_dia, modelo=Solicitud
        ),
        "solicitudes_pendientes": contar(Solicitud.estado == "Pendiente", modelo=Solicitud),
        "cambios_de_plan": contar(
            Solicitud.estado == "Aprobada", Solicitud.id_servicio.is_(None), modelo=Solicitud
        ),
        "tiempo_promedio_respuesta_horas": _tiempo_promedio_de_respuesta(),
        "reclamos_abiertos": contar(
            Reclamo.estado_reclamo == ESTADO_RECLAMO_ABIERTO, modelo=Reclamo
        ),
        "facturas_emitidas": contar(modelo=Factura),
        "importe_facturado": float(importe_facturado),
    }


def generar_metricas_diarias():
    """Calcula las métricas del día y las envía a AnalytixPro (HU-27).

    Devuelve (metricas, respuesta_de_analytixpro).
    """
    metricas = metricas_del_dia()
    respuesta = analytixpro.enviar_metricas(metricas)
    auditoria.registrar(
        "AnalytixPro",
        "enviar_metricas",
        respuesta["ok"],
        f"Métricas del {metricas['fecha']}: {respuesta['recibidas']} valores enviados.",
    )
    return metricas, respuesta


def _tiempo_promedio_de_respuesta():
    """Horas promedio entre que se crea una solicitud y se resuelve (None si no hay)."""
    resueltas = db.session.scalars(
        db.select(Solicitud).where(Solicitud.fecha_resolucion.is_not(None))
    ).all()
    if not resueltas:
        return None
    horas = [
        (s.fecha_resolucion.replace(tzinfo=None) - s.fecha_creacion.replace(tzinfo=None)).total_seconds()
        / 3600
        for s in resueltas
    ]
    return round(sum(horas) / len(horas), 2)
