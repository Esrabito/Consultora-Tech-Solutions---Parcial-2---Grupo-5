"""Pruebas para el registro y listado de reclamos de clientes (HU-18)."""

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