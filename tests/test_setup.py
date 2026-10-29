import pytest

from app import create_app
from config import TestConfig


def test_la_pagina_de_inicio_responde(client):
    respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert "Gestión de Servicios Profesionales" in respuesta.get_data(as_text=True)


def test_la_app_no_arranca_sin_variables_obligatorias():
    class ConfigSinSecretos(TestConfig):
        SECRET_KEY = None
        ADMIN_PASSWORD = None

    with pytest.raises(RuntimeError, match="SECRET_KEY, ADMIN_PASSWORD"):
        create_app(ConfigSinSecretos)


def test_una_ruta_inexistente_devuelve_404_html(client):
    respuesta = client.get("/no-existe")

    assert respuesta.status_code == 404
    assert "no existe" in respuesta.get_data(as_text=True)


def test_una_ruta_api_inexistente_devuelve_404_json(client):
    respuesta = client.get("/api/no-existe")

    assert respuesta.status_code == 404
    assert respuesta.get_json() == {"error": "Recurso no encontrado"}


class TestAccesoAdministrador:
    def test_el_panel_redirige_al_login_si_no_hay_sesion(self, client):
        respuesta = client.get("/admin/")

        assert respuesta.status_code == 302
        assert "/admin/login" in respuesta.headers["Location"]

    def test_contrasena_incorrecta_no_da_acceso(self, client):
        respuesta = client.post("/admin/login", data={"password": "incorrecta"})

        assert respuesta.status_code == 401
        assert "Contraseña incorrecta" in respuesta.get_data(as_text=True)
        assert client.get("/admin/").status_code == 302

    def test_contrasena_correcta_da_acceso_al_panel(self, admin_client):
        respuesta = admin_client.get("/admin/")

        assert respuesta.status_code == 200
        assert "Panel de administración" in respuesta.get_data(as_text=True)

    def test_despues_del_login_vuelve_a_la_pagina_pedida(self, client):
        respuesta = client.post(
            "/admin/login?next=/admin/",
            data={"password": TestConfig.ADMIN_PASSWORD},
        )

        assert respuesta.headers["Location"].endswith("/admin/")

    def test_no_redirige_a_sitios_externos(self, client):
        respuesta = client.post(
            "/admin/login?next=//sitio-malicioso.com",
            data={"password": TestConfig.ADMIN_PASSWORD},
        )

        assert "sitio-malicioso" not in respuesta.headers["Location"]

    def test_cerrar_sesion_quita_el_acceso(self, admin_client):
        admin_client.post("/admin/logout")

        assert admin_client.get("/admin/").status_code == 302


def test_los_formularios_rechazan_pedidos_sin_token_csrf():
    class ConfigConCsrf(TestConfig):
        WTF_CSRF_ENABLED = True

    cliente = create_app(ConfigConCsrf).test_client()
    respuesta = cliente.post("/admin/login", data={"password": TestConfig.ADMIN_PASSWORD})

    assert respuesta.status_code == 400
