"""Comandos de consola de la aplicación.

    flask semilla             carga datos de ejemplo si la base está vacía
    flask semilla --reiniciar borra todo y vuelve a cargar los datos de ejemplo

Los datos pasan por los mismos servicios que usan las pantallas, así que
respetan todas las validaciones. Sirven para la demo de la Sprint Review y para
probar a mano sin cargar todo desde cero.
"""

import click
from flask import Blueprint

from app.extensions import db
from app.models import Cliente, Plan, Servicio
from app.services import clientes as clientes_service
from app.services import planes as planes_service
from app.services import servicios as servicios_service

comandos_bp = Blueprint("comandos", __name__, cli_group=None)

SERVICIOS = ["Consultoría en finanzas", "Asesoría legal", "Marketing digital", "Soporte técnico"]

PLANES = [
    {"nombre_plan": "Plan Básico", "valor_plan": "15000", "servicios": ["Soporte técnico"]},
    {"nombre_plan": "Plan Pyme", "valor_plan": "32500,50", "servicios": ["Consultoría en finanzas", "Soporte técnico"]},
    {
        "nombre_plan": "Plan Empresa",
        "valor_plan": "68000",
        "servicios": ["Consultoría en finanzas", "Asesoría legal", "Marketing digital", "Soporte técnico"],
    },
]

CLIENTES = [
    {"nombre": "Ana Pérez", "dni": "30123456", "email": "ana.perez@example.com", "telefono": "11 4567 8901", "plan": "Plan Pyme"},
    {"nombre": "Bruno Gómez", "dni": "28987654", "email": "bruno.gomez@example.com", "telefono": "11 2345 6789", "plan": "Plan Básico"},
    # DNI con todos los dígitos iguales: VeriCheck lo rechaza. Sirve para mostrar el caso de error.
    {"nombre": "Carla Prueba", "dni": "11111111", "email": "carla.prueba@example.com", "telefono": "11 1111 1111", "plan": "Plan Empresa"},
]


@comandos_bp.cli.command("semilla")
@click.option("--reiniciar", is_flag=True, help="Borra los datos actuales antes de cargar los de ejemplo.")
def semilla(reiniciar):
    """Carga servicios, planes y clientes de ejemplo."""
    if reiniciar:
        db.drop_all()
        db.create_all()
    elif db.session.scalar(db.select(Servicio).limit(1)) is not None:
        click.echo("La base ya tiene datos. Usá --reiniciar para borrarlos y cargar los de ejemplo.")
        return

    servicios = {tipo: servicios_service.crear_servicio({"tipo_servicio": tipo}) for tipo in SERVICIOS}

    planes = {}
    for datos in PLANES:
        ids = [servicios[tipo].id_servicio for tipo in datos["servicios"]]
        planes[datos["nombre_plan"]] = planes_service.crear_plan({**datos, "servicios": ids})

    for datos in CLIENTES:
        cliente = {clave: valor for clave, valor in datos.items() if clave != "plan"}
        cliente["id_plan"] = str(planes[datos["plan"]].id_plan)
        clientes_service.crear_cliente(cliente)

    click.echo(
        f"Listo: {db.session.scalar(db.select(db.func.count(Servicio.id_servicio)))} servicios, "
        f"{db.session.scalar(db.select(db.func.count(Plan.id_plan)))} planes y "
        f"{db.session.scalar(db.select(db.func.count(Cliente.id_cliente)))} clientes de ejemplo."
    )
