"""Modelos de datos basados en el DER de la primera parte del TP.

Vamos agregando cada modelo con la HU que lo necesita y lo importamos acá para
que db.create_all() lo registre.
"""

from app.models.plan import Plan, plan_servicio
from app.models.servicio import Servicio
from app.models.cliente import Cliente

__all__ = ["Plan", "Servicio", "plan_servicio", "Cliente"]
