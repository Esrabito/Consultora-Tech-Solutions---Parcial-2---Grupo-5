from app.extensions import db


class Servicio(db.Model):
    """Servicio del catálogo de la consultora (DER: Servicios)."""

    __tablename__ = "servicios"

    id_servicio = db.Column(db.Integer, primary_key=True)
    tipo_servicio = db.Column(db.String(100), nullable=False, unique=True)

    planes = db.relationship(
        "Plan",
        secondary="plan_servicio",
        back_populates="servicios",
        order_by="Plan.nombre_plan",
    )

    def a_dict(self):
        return {"id_servicio": self.id_servicio, "tipo_servicio": self.tipo_servicio}

    def __repr__(self):
        return f"<Servicio {self.id_servicio} {self.tipo_servicio!r}>"
