"""Pruebas de la simulación de VeriCheck (HU-25)."""

import pytest

from app.integrations import vericheck


def test_un_dni_comun_se_valida():
    assert vericheck.consultar_identidad("12345678", "Ana Pérez") == {
        "valido": True,
        "motivo": None,
    }


@pytest.mark.parametrize("dni", ["11111111", "0000000", "99999999"])
def test_un_dni_con_todos_los_digitos_iguales_no_se_valida(dni):
    resultado = vericheck.consultar_identidad(dni, "Ana Pérez")

    assert resultado == {"valido": False, "motivo": vericheck.MOTIVO_DNI_NO_REGISTRADO}