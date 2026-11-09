"""Pruebas de HU-25 Validar identidad (CU-1): reglas de negocio, sin llamar a VeriCheck real."""

import logging

import pytest

from app.services import validacion
from app.services.errores import DatosInvalidos

DATOS = {"dni": "12345678", "nombre": "Ana Pérez"}


def simular_vericheck(monkeypatch, respuesta):
    llamadas = []

    def consultar_falso(dni, nombre):
        llamadas.append((dni, nombre))
        return respuesta

    monkeypatch.setattr(validacion.vericheck, "consultar_identidad", consultar_falso)
    return llamadas


def errores_de(datos):
    with pytest.raises(DatosInvalidos) as excinfo:
        validacion.validar_identidad(datos)
    return excinfo.value.errores


class TestValidacionCorrecta:
    def test_identidad_valida_devuelve_los_datos_y_el_estado(self, app, monkeypatch):
        simular_vericheck(monkeypatch, {"valido": True, "motivo": None})
        with app.app_context():
            resultado = validacion.validar_identidad(DATOS)

        assert resultado == {
            "dni": "12345678",
            "nombre": "Ana Pérez",
            "estado": "VALIDADO",
            "motivo": None,
        }

    def test_identidad_no_valida_devuelve_el_motivo_de_vericheck(self, app, monkeypatch):
        simular_vericheck(monkeypatch, {"valido": False, "motivo": "El DNI no coincide."})
        with app.app_context():
            resultado = validacion.validar_identidad(DATOS)

        assert resultado["estado"] == "NO_VALIDADO"
        assert resultado["motivo"] == "El DNI no coincide."

    def test_si_vericheck_no_da_motivo_se_usa_uno_por_defecto(self, app, monkeypatch):
        simular_vericheck(monkeypatch, {"valido": False, "motivo": None})
        with app.app_context():
            resultado = validacion.validar_identidad(DATOS)

        assert resultado["motivo"] == validacion.MOTIVO_POR_DEFECTO

    def test_normaliza_el_dni_y_el_nombre_antes_de_consultar(self, app, monkeypatch):
        llamadas = simular_vericheck(monkeypatch, {"valido": True, "motivo": None})
        with app.app_context():
            resultado = validacion.validar_identidad(
                {"dni": "12.345 678", "nombre": "  Ana    Pérez "}
            )

        assert llamadas == [("12345678", "Ana Pérez")]
        assert resultado["dni"] == "12345678"
        assert resultado["nombre"] == "Ana Pérez"


class TestDatosInvalidos:
    @pytest.mark.parametrize("dni", [None, "", "   "])
    def test_dni_obligatorio(self, app, dni):
        with app.app_context():
            errores = errores_de({"dni": dni, "nombre": "Ana Pérez"})
        assert errores == {"dni": "El DNI es obligatorio."}

    @pytest.mark.parametrize("dni", ["123456", "123456789", "12345abc", "1234-5678"])
    def test_dni_con_formato_incorrecto(self, app, dni):
        with app.app_context():
            errores = errores_de({"dni": dni, "nombre": "Ana Pérez"})
        assert "dni" in errores

    def test_dni_que_no_es_texto(self, app):
        with app.app_context():
            errores = errores_de({"dni": 12345678, "nombre": "Ana Pérez"})
        assert errores == {"dni": "El DNI debe ser un texto."}

    @pytest.mark.parametrize("nombre", [None, "", "   "])
    def test_nombre_obligatorio(self, app, nombre):
        with app.app_context():
            errores = errores_de({"dni": "12345678", "nombre": nombre})
        assert errores == {"nombre": "El nombre es obligatorio."}

    @pytest.mark.parametrize("nombre", ["Al", "A" * 101])
    def test_nombre_con_largo_incorrecto(self, app, nombre):
        with app.app_context():
            errores = errores_de({"dni": "12345678", "nombre": nombre})
        assert "nombre" in errores

    def test_informa_todos_los_errores_juntos(self, app):
        with app.app_context():
            errores = errores_de({})
        assert set(errores) == {"dni", "nombre"}

    def test_con_datos_invalidos_no_se_llama_a_vericheck(self, app, monkeypatch):
        llamadas = simular_vericheck(monkeypatch, {"valido": True, "motivo": None})
        with app.app_context():
            errores_de({"dni": "abc", "nombre": ""})
        assert llamadas == []


class TestRegistroEnElLog:
    def test_registra_el_resultado_sin_guardar_el_dni_completo(self, app, monkeypatch, caplog):
        simular_vericheck(monkeypatch, {"valido": True, "motivo": None})
        caplog.set_level(logging.INFO)
        with app.app_context():
            validacion.validar_identidad(DATOS)

        assert "VALIDADO" in caplog.text
        assert "*****678" in caplog.text
        assert "12345678" not in caplog.text