"""Archivos adjuntos de las solicitudes (HU-10).

El cliente puede adjuntar un PDF o una imagen. Se controla la extensión, que el
contenido corresponda a ese tipo y el tamaño, y se guarda con un nombre generado
por el sistema (el nombre que trae el cliente no se usa para guardar nada).
"""

import os
import uuid

from flask import current_app

from app.services.errores import DatosInvalidos, NoEncontrado

TAMANIO_MAXIMO = 2 * 1024 * 1024  # 2 MB

# extensión -> comienzos válidos del archivo (los primeros bytes identifican el formato)
FORMATOS = {
    "pdf": (b"%PDF",),
    "png": (b"\x89PNG",),
    "jpg": (b"\xff\xd8",),
    "jpeg": (b"\xff\xd8",),
}


def guardar(archivo):
    """Valida y guarda el archivo. Devuelve el nombre guardado, o None si no se adjuntó nada."""
    if archivo is None or not archivo.filename:
        return None

    extension = os.path.splitext(archivo.filename)[1].lstrip(".").lower()
    if extension not in FORMATOS:
        raise DatosInvalidos({"adjunto": "El adjunto debe ser un PDF o una imagen (PNG o JPG)."})

    contenido = archivo.read(TAMANIO_MAXIMO + 1)
    if not contenido:
        raise DatosInvalidos({"adjunto": "El archivo adjunto está vacío."})
    if len(contenido) > TAMANIO_MAXIMO:
        raise DatosInvalidos({"adjunto": "El adjunto no puede pesar más de 2 MB."})
    if not contenido.startswith(FORMATOS[extension]):
        raise DatosInvalidos({"adjunto": "El contenido del archivo no corresponde a su tipo."})

    carpeta = current_app.config["ADJUNTOS_DIR"]
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"{uuid.uuid4().hex}.{extension}"
    with open(os.path.join(carpeta, nombre), "wb") as destino:
        destino.write(contenido)
    return nombre


def carpeta_de_adjuntos():
    return current_app.config["ADJUNTOS_DIR"]


def nombre_de_adjunto(solicitud):
    if not solicitud.adjunto:
        raise NoEncontrado("La solicitud no tiene archivo adjunto.")
    return solicitud.adjunto
