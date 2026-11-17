"""Facturas por cambio de plan (HU-15 y HU-32).

Cuando el administrador aprueba un cambio de plan, el sistema le envía a PagoNet
(simulado en app/integrations/pagonet.py) los datos del cliente, el nuevo plan y el
importe, y PagoNet devuelve la factura. Si PagoNet no responde, la solicitud sigue
pendiente y el plan del cliente no cambia (HU-16: el plan se actualiza luego de la
factura).
"""

from app.extensions import db
from app.integrations import pagonet
from app.models import Factura
from app.services import auditoria
from app.services.errores import Conflicto, NoEncontrado


def listar_facturas():
    """Todas las facturas emitidas, las más nuevas primero (HU-32)."""
    return db.session.scalars(db.select(Factura).order_by(Factura.id_factura.desc())).all()


def obtener_factura(id_factura):
    factura = db.session.get(Factura, id_factura)
    if factura is None:
        raise NoEncontrado("La factura no existe.")
    return factura


def emitir_por_cambio_de_plan(solicitud):
    """Pide la factura a PagoNet y la deja agregada a la sesión, sin guardar todavía.

    Quien la llama guarda todo junto (factura, estado de la solicitud y plan nuevo).
    Si PagoNet falla lanza Conflicto y no queda nada para guardar.
    """
    cliente = solicitud.cliente
    plan = solicitud.plan_solicitado

    respuesta = pagonet.generar_factura(
        {
            "email": cliente.email,
            "cliente": cliente.nombre,
            "plan": plan.nombre_plan,
            "importe": float(plan.valor_plan),
        }
    )

    if not respuesta["ok"]:
        auditoria.registrar(
            "PagoNet",
            "generar_factura",
            False,
            f"Solicitud {solicitud.id_solicitud}: {respuesta['motivo']}",
        )
        raise Conflicto(f"{respuesta['motivo']} La solicitud sigue pendiente.")

    auditoria.registrar(
        "PagoNet",
        "generar_factura",
        True,
        f"Solicitud {solicitud.id_solicitud}: factura {respuesta['numero']}.",
    )
    factura = Factura(
        numero=respuesta["numero"],
        importe=plan.valor_plan,
        id_cliente=cliente.id_cliente,
        id_plan=plan.id_plan,
        id_solicitud=solicitud.id_solicitud,
    )
    db.session.add(factura)
    return factura
