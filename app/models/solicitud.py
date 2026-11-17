from datetime import datetime, timezone

from app.extensions import db


class Solicitud(db.Model):
    """Solicitud realizada por un cliente."""

    __tablename__ = "solicitudes"

    id_solicitud = db.Column(db.Integer, primary_key=True)
    fecha_creacion = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    estado = db.Column(db.String(20), nullable=False, default="Pendiente")
    adjunto = db.Column(db.String(255), nullable=True)
    motivo = db.Column(db.String(500), nullable=False)
    tipo_modificacion = db.Column(db.String(50), nullable=False)
    resultado = db.Column(db.String(500), nullable=True)
    # HU-13: la define el administrador; si no la cambia, queda en "Media".
    prioridad = db.Column(db.String(10), nullable=False, default="Media")
    # Se completa al aprobar o rechazar; sirve para el tiempo de respuesta (HU-27).
    fecha_resolucion = db.Column(db.DateTime, nullable=True)

    id_cliente = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id_cliente", ondelete="CASCADE"),
        nullable=False,
    )
    id_plan_actual = db.Column(
        db.Integer,
        db.ForeignKey("planes.id_plan", ondelete="RESTRICT"),
        nullable=False,
    )
    id_plan_solicitado = db.Column(
        db.Integer,
        db.ForeignKey("planes.id_plan", ondelete="RESTRICT"),
        nullable=False,
    )
    id_servicio = db.Column(
        db.Integer,
        db.ForeignKey("servicios.id_servicio", ondelete="RESTRICT"),
        nullable=True,
    )

    cliente = db.relationship("Cliente", back_populates="solicitudes")
    plan_actual = db.relationship("Plan", foreign_keys=[id_plan_actual])
    plan_solicitado = db.relationship("Plan", foreign_keys=[id_plan_solicitado])
    servicio = db.relationship("Servicio")

    def a_dict(self):
        return {
            "id_solicitud": self.id_solicitud,
            "id_cliente": self.id_cliente,
            "tipo_modificacion": self.tipo_modificacion,
            "estado": self.estado,
            "motivo": self.motivo,
            "resultado": self.resultado,
            "prioridad": self.prioridad,
            "fecha_creacion": self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            "plan_actual": self.plan_actual.nombre_plan,
            "plan_solicitado": self.plan_solicitado.nombre_plan,
            "servicio": self.servicio.tipo_servicio if self.servicio else None,
        }

    def __repr__(self):
        return f"<Solicitud {self.id_solicitud} {self.estado!r}>"
