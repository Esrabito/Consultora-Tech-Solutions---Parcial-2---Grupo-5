import os
import tempfile

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

    # Flask-SQLAlchemy ubica las rutas SQLite relativas dentro de la carpeta instance/
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///tech_solutions.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # HU-10: archivos adjuntos de las solicitudes. Se guardan fuera del código, en instance/.
    ADJUNTOS_DIR = os.path.join(BASE_DIR, "instance", "adjuntos")
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "clave-solo-para-tests"
    ADMIN_PASSWORD = "admin-test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # En los tests mandamos formularios sin token CSRF; la protección la probamos aparte.
    WTF_CSRF_ENABLED = False
    # Los adjuntos de las pruebas van a una carpeta temporal, no a instance/.
    ADJUNTOS_DIR = tempfile.mkdtemp(prefix="adjuntos-test-")