import sqlite3

from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
csrf = CSRFProtect()


@event.listens_for(Engine, "connect")
def _activar_claves_foraneas_sqlite(dbapi_connection, _connection_record):
    # SQLite no controla las claves foráneas por defecto, así que las activamos en cada
    # conexión para mantener la integridad de los datos (RNF-11).
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
