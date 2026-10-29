import pytest

from app import create_app
from app.extensions import db
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(client):
    respuesta = client.post("/admin/login", data={"password": TestConfig.ADMIN_PASSWORD})
    assert respuesta.status_code == 302
    return client
