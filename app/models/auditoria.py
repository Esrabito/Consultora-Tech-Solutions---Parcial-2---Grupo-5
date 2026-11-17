from datetime import datetime, timezone

from app.extensions import db


class AuditoriaIntegracion(db.Model):
    """Registro de cada comunicación con un sistema externo (HU-29)."""

    __tablename__ = "auditoria_integraciones"

    id_auditoria = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    sistema = db.Column(db.String(30), nullable=False)
    operacion = db.Column(db.String(60), nullable=False)
    # "OK" si el sistema respondió bien, "ERROR" si falló o no estaba disponible.
    resultado = db.Column(db.String(10), nullable=False)
    detalle = db.Column(db.String(300), nullable=True)

    def a_dict(self):
        return {
            "id_auditoria": self.id_auditoria,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "sistema": self.sistema,
            "operacion": self.operacion,
            "resultado": self.resultado,
            "detalle": self.detalle,
        }

    def __repr__(self):
        return f"<Auditoria {self.id_auditoria} {self.sistema} {self.resultado}>"
