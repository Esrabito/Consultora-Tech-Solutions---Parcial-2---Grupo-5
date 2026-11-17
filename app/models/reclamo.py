from datetime import datetime, timezone

from app.extensions import db


class Reclamo(db.Model):
    """Reclamo registrado por un cliente (DER: Reclamos)."""

    __tablename__ = "reclamos"

    id_reclamo = db.Column(db.Integer, primary_key=True)
    fecha_creacion = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    mensaje_reclamo = db.Column(db.String(500), nullable=False)
    estado_reclamo = db.Column(db.String(20), nullable=False, default="Pendiente")
    mensaje_respuesta = db.Column(db.String(500), nullable=True)

    id_cliente = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id_cliente", ondelete="CASCADE"),
        nullable=False,
    )

    cliente = db.relationship("Cliente", back_populates="reclamos")

    def a_dict(self):
        return {
            "id_reclamo": self.id_reclamo,
            "id_cliente": self.id_cliente,
            "mensaje_reclamo": self.mensaje_reclamo,
            "estado_reclamo": self.estado_reclamo,
            "mensaje_respuesta": self.mensaje_respuesta,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
        }

    def __repr__(self):
        return f"<Reclamo {self.id_reclamo} {self.estado_reclamo!r}>"