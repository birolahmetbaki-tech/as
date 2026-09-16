"""Test ortami: her test oturumu icin ayri ve gecici bir veritabani kullanilir."""

import os
import tempfile
from pathlib import Path

import pytest

TEST_PASSWORD = "test-parola-123"

_tmp_dir = tempfile.mkdtemp(prefix="enerji-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp_dir) / 'test.db'}"
os.environ["SECRET_KEY"] = "test-secret-key"

from app.security import hash_password  # noqa: E402

os.environ["APP_PASSWORD_HASH"] = hash_password(TEST_PASSWORD)

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def database():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def logged_in_client(client):
    response = client.post("/giris", data={"password": TEST_PASSWORD})
    assert response.status_code == 200
    return client
