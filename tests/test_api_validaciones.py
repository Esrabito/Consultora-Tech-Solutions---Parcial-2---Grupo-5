"""Pruebas del endpoint POST /api/validaciones (HU-25)."""


def test_validar_identidad_exitosa(client):
    respuesta = client.post(
        "/api/validaciones",
        json={"dni": "12345678", "nombre": "Ana Pérez"},
    )
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos["dni"] == "12345678"
    assert datos["nombre"] == "Ana Pérez"
    assert datos["estado"] == "VALIDADO"
    assert datos["motivo"] is None


def test_validar_identidad_no_validada_por_vericheck(client):
    respuesta = client.post(
        "/api/validaciones",
        json={"dni": "00000000", "nombre": "Ana Pérez"},
    )
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos["estado"] == "NO_VALIDADO"
    assert "persona registrada" in datos["motivo"]


def test_validar_identidad_datos_invalidos_retorna_400(client):
    respuesta = client.post(
        "/api/validaciones",
        json={"dni": "", "nombre": "A"},
    )
    assert respuesta.status_code == 400
    datos = respuesta.get_json()
    assert "detalles" in datos
    assert "dni" in datos["detalles"]
    assert "nombre" in datos["detalles"]