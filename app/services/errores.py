"""Errores de negocio que pueden mostrarse al usuario.

Las rutas HTML los convierten en mensajes del formulario y la API los convierte
en respuestas JSON con el código HTTP que corresponde.
"""


class ErrorDeNegocio(Exception):
    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


class DatosInvalidos(ErrorDeNegocio):
    """Uno o más campos no cumplen las reglas. HTTP 400."""

    def __init__(self, errores):
        super().__init__("Los datos ingresados no son válidos.")
        self.errores = errores


class NoEncontrado(ErrorDeNegocio):
    """El recurso pedido no existe. HTTP 404."""


class Conflicto(ErrorDeNegocio):
    """El dato ya existe o está en uso. HTTP 409."""

    def __init__(self, mensaje, campo=None):
        super().__init__(mensaje)
        self.campo = campo


def errores_para_formulario(error):
    """Devuelve los errores como {campo: mensaje} para mostrarlos en un formulario."""
    if isinstance(error, DatosInvalidos):
        return error.errores
    if isinstance(error, Conflicto) and error.campo:
        return {error.campo: error.mensaje}
    return {"general": error.mensaje}
