"""Simulación de VeriCheck (HU-25 / CU-1 Validar información personal).

VeriCheck es un sistema externo que no existe. Por indicación del profesor, su
funcionamiento se simula dentro de nuestro propio código. Este módulo es el único
que sabe cómo se decide si una identidad es válida: si algún día se conectara un
VeriCheck real, solo habría que cambiar el interior de consultar_identidad().

Regla simulada (suposición del grupo): un DNI con todos los dígitos iguales
(por ejemplo 11111111) no corresponde a una persona registrada.
"""

MOTIVO_DNI_NO_REGISTRADO = "El DNI no corresponde a una persona registrada."


def consultar_identidad(dni, nombre):
    """Simula la consulta a VeriCheck con un DNI y un nombre ya validados.

    Devuelve {"valido": bool, "motivo": str | None}. El nombre se recibe porque
    así sería la consulta real, aunque la regla simulada solo mira el DNI.
    """
    if len(set(dni)) == 1:
        return {"valido": False, "motivo": MOTIVO_DNI_NO_REGISTRADO}
    return {"valido": True, "motivo": None}