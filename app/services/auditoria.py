"""Auditoría de integraciones con sistemas externos (HU-29).

Cada vez que el sistema habla con VeriCheck, CRMMax, PagoNet, NotiSys o AnalytixPro
queda un registro con el sistema, la operación, el resultado y un detalle. Es el
paso siguiente al log básico que acordó el grupo (decisión 3).
"""

from app.extensions import db
from app.models import AuditoriaIntegracion
from app.services.comun import guardar_cambios

RESULTADO_OK = "OK"
RESULTADO_ERROR = "ERROR"

LIMITE_LISTADO = 200


def registrar(sistema, operacion, ok, detalle=""):
    registro = AuditoriaIntegracion(
        sistema=sistema,
        operacion=operacion,
        resultado=RESULTADO_OK if ok else RESULTADO_ERROR,
        detalle=(detalle or "")[:300],
    )
    db.session.add(registro)
    guardar_cambios()
    return registro


def listar(sistema=None):
    """Los últimos registros, los más nuevos primero. Se puede filtrar por sistema."""
    consulta = db.select(AuditoriaIntegracion)
    if sistema:
        consulta = consulta.where(AuditoriaIntegracion.sistema == sistema)
    consulta = consulta.order_by(AuditoriaIntegracion.id_auditoria.desc()).limit(LIMITE_LISTADO)
    return db.session.scalars(consulta).all()


def sistemas_registrados():
    consulta = db.select(AuditoriaIntegracion.sistema).distinct().order_by(AuditoriaIntegracion.sistema)
    return db.session.scalars(consulta).all()
