"""Pruebas de la sincronización de clientes con CRMMax simulado (HU-30)."""

import logging

import pytest

from app.extensions import db
from app.integrations import crmmax
from app.models import Cliente, Plan


@pytest.fixture
def con_plan(app):
    with app.app_context():
        db.session.add(Plan(nombre_plan="Plan Básico", valor_plan=15000))
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


def cantidad_de_clientes(app):
    with app.app_context():
        return db.session.scalar(db.select(db.func.count(Cliente.id_cliente)))


class TestSimulacion:
    def test_acepta_un_cliente_normal(self):
        respuesta = crmmax.registrar_cliente({"email": "ana@example.com"})

        assert respuesta == {"ok": True, "motivo": None}

    def test_rechaza_el_dominio_caido_sin_importar_mayusculas(self):
        respuesta = crmmax.registrar_cliente({"email": "Ana@CRMMAX-caido.test"})

        assert respuesta["ok"] is False
        assert respuesta["motivo"] == crmmax.MOTIVO_NO_DISPONIBLE


class TestRegistroConCRMMax:
    def test_registro_correcto_se_envia_a_crmmax_y_queda_en_el_log(
        self, app, con_plan, caplog
    ):
        with caplog.at_level(logging.INFO):
            respuesta = con_plan.post("/cliente/registro", data=datos_cliente())

        assert respuesta.status_code == 302
        assert cantidad_de_clientes(app) == 1
        assert "CRMMax: cliente 1 registrado (plan Plan Básico)" in caplog.text

    def test_si_crmmax_falla_el_cliente_queda_registrado_y_se_avisa(
        self, app, con_plan, caplog
    ):
        datos = datos_cliente(email="ana@crmmax-caido.test")

        with caplog.at_level(logging.INFO):
            respuesta = con_plan.post("/cliente/registro", data=datos, follow_redirects=True)

        html = respuesta.get_data(as_text=True)
        assert cantidad_de_clientes(app) == 1
        assert "Registro de Ana Pérez completado correctamente." in html
        assert "CRMMax no está disponible en este momento." in html
        assert "no se pudo registrar el cliente 1" in caplog.text

    def test_un_registro_invalido_no_llama_a_crmmax(self, app, con_plan, caplog):
        with caplog.at_level(logging.INFO):
            respuesta = con_plan.post("/cliente/registro", data=datos_cliente(dni=""))

        assert respuesta.status_code == 400
        assert cantidad_de_clientes(app) == 0
        assert "CRMMax" not in caplog.text
