from datetime import datetime, timezone

from app.extensions import db


class Factura(db.Model):
    """Factura generada por PagoNet al aprobar un cambio de plan (HU-15)."""

    __tablename__ = "facturas"

    id_factura = db.Column(db.Integer, primary_key=True)
    # Número que devuelve PagoNet; no se repite.
    numero = db.Column(db.String(30), nullable=False, unique=True)
    fecha_emision = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    # Numeric y no Float para no perder centavos.
    importe = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="Emitida")

    id_cliente = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id_cliente", ondelete="CASCADE"),
        nullable=False,
    )
    id_plan = db.Column(
        db.Integer,
        db.ForeignKey("planes.id_plan", ondelete="RESTRICT"),
        nullable=False,
    )
    id_solicitud = db.Column(
        db.Integer,
        db.ForeignKey("solicitudes.id_solicitud", ondelete="SET NULL"),
        nullable=True,
    )

    cliente = db.relationship("Cliente")
    plan = db.relationship("Plan")
    solicitud = db.relationship("Solicitud")

    def a_dict(self):
        return {
            "id_factura": self.id_factura,
            "numero": self.numero,
            "fecha_emision": self.fecha_emision.isoformat() if self.fecha_emision else None,
            "importe": float(self.importe),
            "estado": self.estado,
            "id_cliente": self.id_cliente,
            "cliente": self.cliente.nombre,
            "plan": self.plan.nombre_plan,
            "id_solicitud": self.id_solicitud,
        }

    def __repr__(self):
        return f"<Factura {self.numero}>"
