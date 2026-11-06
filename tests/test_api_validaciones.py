"""Pruebas del endpoint de HU-25 (POST /api/validaciones). VeriCheck se simula."""

from app.services import validacion
from app.services.errores import VeriCheckNoDisponible

DATOS = {"dni": "12345678", "nombre": "Ana Pérez"}


def simular_vericheck(monkeypatch, respuesta=None, error=None):
    def consultar_falso(dni, nombre):
        if error:
            raise error
        return respuesta

    monkeypatch.setattr(validacion.vericheck, "consultar_identidad", consultar_falso)


class TestApiValidaciones:
    def test_identidad_valida_devuelve_200_con_el_estado(self, admin_client, monkeypatch):
        simular_vericheck(monkeypatch, {"valido": True, "motivo": None})

        respuesta = admin_client.post("/api/validaciones", json=DATOS)

        assert respuesta.status_code == 200
        assert respuesta.get_json() == {
            "dni": "12345678",
            "nombre": "Ana Pérez",
            "estado": "VALIDADO",
            "motivo": None,
        }

    def test_identidad_no_valida_tambien_devuelve_200_con_el_motivo(self, admin_client, monkeypatch):
        simular_vericheck(monkeypatch, {"valido": False, "motivo": "El DNI no coincide."})

        respuesta = admin_client.post("/api/validaciones", json=DATOS)

        assert respuesta.status_code == 200
        assert respuesta.get_json()["estado"] == "NO_VALIDADO"
        assert respuesta.get_json()["motivo"] == "El DNI no coincide."

    def test_datos_invalidos_devuelven_400_con_detalle(self, admin_client):
        respuesta = admin_client.post("/api/validaciones", json={"dni": "abc"})

        assert respuesta.status_code == 400
        assert set(respuesta.get_json()["detalles"]) == {"dni", "nombre"}

    def test_vericheck_caido_devuelve_502(self, admin_client, monkeypatch):
        simular_vericheck(monkeypatch, error=VeriCheckNoDisponible("VeriCheck no respondió."))

        respuesta = admin_client.post("/api/validaciones", json=DATOS)

        assert respuesta.status_code == 502
        assert respuesta.get_json() == {"error": "VeriCheck no respondió."}

    def test_funciona_de_punta_a_punta_con_la_validacion_simulada(self, admin_client):
        valido = admin_client.post("/api/validaciones", json=DATOS)
        rechazado = admin_client.post(
            "/api/validaciones", json={"dni": "11111111", "nombre": "Ana Pérez"}
        )

        assert valido.get_json()["estado"] == "VALIDADO"
        assert rechazado.get_json()["estado"] == "NO_VALIDADO"

    def test_rechaza_cuerpos_que_no_son_json(self, admin_client):
        respuesta = admin_client.post("/api/validaciones", data="dni=12345678")

        assert respuesta.status_code == 415

    def test_rechaza_json_que_no_es_un_objeto(self, admin_client):
        respuesta = admin_client.post("/api/validaciones", json=["12345678"])

        assert respuesta.status_code == 400

    def test_sin_sesion_de_admin_devuelve_401(self, client):
        respuesta = client.post("/api/validaciones", json=DATOS)

        assert respuesta.status_code == 401
        assert respuesta.get_json() == {"error": "No autorizado"}