from app.extensions import db


class Cliente(db.Model):
    """Cliente registrado en el sistema (DER: Clientes)."""

    __tablename__ = "clientes"

    id_cliente = db.Column(db.Integer, primary_key=True)
    #Se pone número para no pasarnos de valores
    dni = db.Column(db.String(8),nullable=False,unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    telefono = db.Column(db.String(30), nullable=False)

    # Un cliente siempre debe tener un plan contratado
    id_plan = db.Column(
        db.Integer,
        db.ForeignKey("planes.id_plan", ondelete="RESTRICT"),
        nullable=False
    )

    # Relación N:1
    # Muchos clientes pueden tener el mismo plan
    plan = db.relationship(
        "Plan",
        backref=db.backref(
            "clientes",
            lazy=True
        )
    )

    def a_dict(self):
        return {
            "id_cliente": self.id_cliente,
            "dni": self.dni,
            "nombre": self.nombre,
            "email": self.email,
            "telefono": self.telefono,
            "id_plan": self.id_plan,
            "nombre_plan": self.plan.nombre_plan if self.plan else None
        }

    def __repr__(self):
        return f"<Cliente {self.id_cliente} {self.nombre!r}>"