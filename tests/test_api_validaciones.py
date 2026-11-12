"""Pruebas del endpoint de HU-25 (POST /api/validaciones), con la validación simulada real."""

from app.integrations import vericheck

VALIDO = {"dni": "12345678", "nombre": "Ana Pérez"}
RECHAZADO = {"dni": "11111111", "nombre": "Ana Pérez"}


class TestApiValidaciones:
    def test_identidad_valida_devuelve_200_con_el_estado(self, admin_client):
        respuesta = admin_client.post("/api/validaciones", json=VALIDO)

        assert respuesta.status_code == 200
        assert respuesta.get_json() == {
            "dni": "12345678",
            "nombre": "Ana Pérez",
            "estado": "VALIDADO",
            "motivo": None,
        }

    def test_identidad_no_valida_tambien_devuelve_200_con_el_motivo(self, admin_client):
        respuesta = admin_client.post("/api/validaciones", json=RECHAZADO)

        assert respuesta.status_code == 200
        assert respuesta.get_json()["estado"] == "NO_VALIDADO"
        assert respuesta.get_json()["motivo"] == vericheck.MOTIVO_DNI_NO_REGISTRADO

    def test_datos_invalidos_devuelven_400_con_detalle(self, admin_client):
        respuesta = admin_client.post("/api/validaciones", json={"dni": "abc"})

        assert respuesta.status_code == 400
        assert set(respuesta.get_json()["detalles"]) == {"dni", "nombre"}

    def test_rechaza_cuerpos_que_no_son_json(self, admin_client):
        respuesta = admin_client.post("/api/validaciones", data="dni=12345678")

        assert respuesta.status_code == 415

    def test_rechaza_json_que_no_es_un_objeto(self, admin_client):
        respuesta = admin_client.post("/api/validaciones", json=["12345678"])

        assert respuesta.status_code == 400

    def test_sin_sesion_de_admin_devuelve_401(self, client):
        respuesta = client.post("/api/validaciones", json=VALIDO)

        assert respuesta.status_code == 401
        assert respuesta.get_json() == {"error": "No autorizado"}