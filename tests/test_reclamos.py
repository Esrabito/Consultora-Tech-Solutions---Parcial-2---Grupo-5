"""Pruebas para el registro y listado de reclamos de clientes (HU-18 / HU-37)."""

import pytest

from app.extensions import db
from app.models import Cliente, Plan, Servicio, Reclamo


@pytest.fixture
def id_cliente_prueba(app):
    with app.app_context():
        servicio = Servicio(tipo_servicio="Soporte técnico")
        db.session.add(servicio)
        db.session.commit()

        plan = Plan(nombre_plan="Plan de Prueba", valor_plan=1000.0, servicios=[servicio])
        db.session.add(plan)
        db.session.commit()

        cliente = Cliente(
            dni="30111222",
            nombre="Test Client",
            email="test.client@example.com",
            telefono="1112345678",
            id_plan=plan.id_plan,
        )
        db.session.add(cliente)
        db.session.commit()
        return cliente.id_cliente


def test_reclamos_requieren_sesion(client):
    """Las rutas de reclamos exigen que el cliente haya ingresado."""
    respuesta = client.get("/cliente/reclamos")
    assert respuesta.status_code == 302
    assert "/cliente/ingresar" in respuesta.headers["Location"]

    respuesta_nuevo = client.get("/cliente/reclamo")
    assert respuesta_nuevo.status_code == 302
    assert "/cliente/ingresar" in respuesta_nuevo.headers["Location"]


def test_registro_y_listado_de_reclamo(client, id_cliente_prueba):
    """Permite registrar un reclamo válido y consultarlo en el listado."""
    with client.session_transaction() as session:
        session["id_cliente"] = id_cliente_prueba

    # Registrar reclamo vía POST
    respuesta = client.post(
        "/cliente/reclamo",
        data={"mensaje_reclamo": "Este es un reclamo de prueba válido para verificar el funcionamiento."},
        follow_redirects=True,
    )
    assert respuesta.status_code == 200
    assert b"registrado correctamente" in respuesta.data

    # Verificar que el reclamo figure en la sección "Mis reclamos"
    respuesta_lista = client.get("/cliente/reclamos")
    assert respuesta_lista.status_code == 200
    assert b"Este es un reclamo de prueba" in respuesta_lista.data
    assert b"Pendiente" in respuesta_lista.data


def test_reclamo_invalido_fuera_de_rango(client, id_cliente_prueba):
    """Rechaza reclamos vacíos o con menos de 5 caracteres."""
    with client.session_transaction() as session:
        session["id_cliente"] = id_cliente_prueba

    respuesta = client.post(
        "/cliente/reclamo",
        data={"mensaje_reclamo": "Mal"},
    )
    assert respuesta.status_code == 400
    assert b"debe tener entre" in respuesta.data


def test_cliente_ve_solo_sus_propios_reclamos(client, app):
    """Verifica que un cliente solo visualice sus reclamos y no los de otros usuarios."""
    with app.app_context():
        servicio = Servicio(tipo_servicio="Soporte Red")
        db.session.add(servicio)
        db.session.commit()

        plan = Plan(nombre_plan="Plan Test", valor_plan=2000.0, servicios=[servicio])
        db.session.add(plan)
        db.session.commit()

        cliente1 = Cliente(
            dni="11222333",
            nombre="Cliente Uno",
            email="uno@example.com",
            telefono="111111111",
            id_plan=plan.id_plan,
        )
        cliente2 = Cliente(
            dni="44555666",
            nombre="Cliente Dos",
            email="dos@example.com",
            telefono="222222222",
            id_plan=plan.id_plan,
        )
        db.session.add_all([cliente1, cliente2])
        db.session.commit()

        reclamo1 = Reclamo(
            id_cliente=cliente1.id_cliente,
            mensaje_reclamo="Este es el reclamo privado del cliente uno.",
        )
        reclamo2 = Reclamo(
            id_cliente=cliente2.id_cliente,
            mensaje_reclamo="Este es el reclamo privado del cliente dos.",
        )
        db.session.add_all([reclamo1, reclamo2])
        db.session.commit()

        id_c1 = cliente1.id_cliente
        id_c2 = cliente2.id_cliente

    
    with client.session_transaction() as session:
        session["id_cliente"] = id_c1

    respuesta1 = client.get("/cliente/reclamos")
    assert respuesta1.status_code == 200
    assert b"reclamo privado del cliente uno" in respuesta1.data
    assert b"reclamo privado del cliente dos" not in respuesta1.data

    
    with client.session_transaction() as session:
        session["id_cliente"] = id_c2

    respuesta2 = client.get("/cliente/reclamos")
    assert respuesta2.status_code == 200
    assert b"reclamo privado del cliente dos" in respuesta2.data
    assert b"reclamo privado del cliente uno" not in respuesta2.data