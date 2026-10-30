"""Modelos de datos basados en el DER de la primera parte del TP.

Vamos agregando cada modelo con la HU que lo necesita y lo importamos acá para
que db.create_all() lo registre.
"""

from app.models.servicio import Servicio

__all__ = ["Servicio"]
