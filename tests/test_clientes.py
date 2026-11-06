"""Pruebas del registro web de clientes (HU-01)."""

import pytest

from app.extensions import db
from app.models import Cliente, Plan


@pytest.fixture
def con_plan(app):
    with app.app_context():
        plan = Plan(nombre_plan="Plan Básico", valor_plan=15000)
        db.session.add(plan)
        db.session.commit()
    return app.test_client()


def datos_cliente(**cambios):
    datos = {
        "dni": "12345678",
        "nombre": "Ana Pérez",
        "email": "ana@example.com",
        "telefono": "1122334455",
        "id_plan": "1",
    }
    datos.update(cambios)
    return datos


def cliente_guardado(app):
    with app.app_context():
        return db.session.scalar(db.select(Cliente))


def test_muestra_el_formulario_de_registro_y_los_planes(con_plan):
    respuesta = con_plan.get("/cliente/registro")

    assert respuesta.status_code == 200
    contenido = respuesta.get_data(as_text=True)
    assert "Registro de cliente" in contenido
    assert "Plan Básico" in contenido


def test_registro_correcto_guarda_el_cliente_y_redirige(app, con_plan):
    respuesta = con_plan.post("/cliente/registro", data=datos_cliente())

    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/")

    cliente = cliente_guardado(app)
    assert cliente.dni == "12345678"
    assert cliente.nombre == "Ana Pérez"
    assert cliente.email == "ana@example.com"
    assert cliente.telefono == "1122334455"
    assert cliente.id_plan == 1


def test_no_permite_registro_sin_elegir_plan(con_plan, app):
    respuesta = con_plan.post(
        "/cliente/registro",
        data=datos_cliente(id_plan=""),
    )

    assert respuesta.status_code == 400
    assert "Seleccioná un plan válido." in respuesta.get_data(as_text=True)
    assert cliente_guardado(app) is None


@pytest.mark.parametrize(
    ("campo", "valor", "mensaje"),
    [
        ("dni", "", "El DNI es obligatorio."),
        ("dni", "123", "entre 7 y 8 números"),
        ("dni", "12A45678", "entre 7 y 8 números"),
        ("nombre", "", "El nombre es obligatorio."),
        ("nombre", "AB", "entre 3 y 100 caracteres"),
        ("email", "", "El email es obligatorio."),
        ("email", "correo-invalido", "formato válido"),
        ("telefono", "", "El teléfono es obligatorio."),
        ("telefono", "1" * 31, "no puede superar los 30 caracteres"),
        ("id_plan", "", "Seleccioná un plan válido."),
        ("id_plan", "99", "El plan seleccionado no existe."),
    ],
)
def test_datos_invalidos_no_guardan_el_cliente(con_plan, app, campo, valor, mensaje):
    respuesta = con_plan.post(
        "/cliente/registro",
        data=datos_cliente(**{campo: valor}),
    )

    assert respuesta.status_code == 400
    assert mensaje in respuesta.get_data(as_text=True)
    assert cliente_guardado(app) is None


def test_el_formulario_conserva_los_datos_si_hay_un_error(con_plan):
    respuesta = con_plan.post(
        "/cliente/registro",
        data=datos_cliente(email="correo-invalido"),
    )

    contenido = respuesta.get_data(as_text=True)
    assert "Ana Pérez" in contenido
    assert "12345678" in contenido
    assert "correo-invalido" in contenido
