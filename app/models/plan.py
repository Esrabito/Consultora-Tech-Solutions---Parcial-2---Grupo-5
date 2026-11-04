from app.extensions import db

# Relación N:M "Incluye" del DER: un plan incluye uno o más servicios y un servicio
# puede estar en varios planes.
# Si se borra el plan, se borran sus filas acá (CASCADE). Un servicio que está en
# un plan no se puede borrar (RESTRICT, CU-15 E2); la regla se controla también en
# app/services/servicios.py para poder mostrar un mensaje claro.
plan_servicio = db.Table(
    "plan_servicio",
    db.Column("id_plan", db.Integer, db.ForeignKey("planes.id_plan", ondelete="CASCADE"), primary_key=True),
    db.Column(
        "id_servicio",
        db.Integer,
        db.ForeignKey("servicios.id_servicio", ondelete="RESTRICT"),
        primary_key=True,
    ),
)


class Plan(db.Model):
    """Plan comercial de la consultora (DER: Planes)."""

    __tablename__ = "planes"

    id_plan = db.Column(db.Integer, primary_key=True)
    nombre_plan = db.Column(db.String(100), nullable=False, unique=True)
    # Numeric y no Float para que los importes no pierdan centavos por redondeo.
    valor_plan = db.Column(db.Numeric(10, 2), nullable=False)

    servicios = db.relationship(
        "Servicio",
        secondary=plan_servicio,
        back_populates="planes",
        order_by="Servicio.tipo_servicio",
    )

    def a_dict(self):
        return {
            "id_plan": self.id_plan,
            "nombre_plan": self.nombre_plan,
            "valor_plan": float(self.valor_plan),
            "servicios": [servicio.a_dict() for servicio in self.servicios],
        }

    def __repr__(self):
        return f"<Plan {self.id_plan} {self.nombre_plan!r}>"
