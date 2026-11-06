import pytest
from fastapi.testclient import TestClient

from src.api.main import crear_app
from src.infrastructure.database import make_engine, make_session_factory
from src.infrastructure.seed import cargar_datos


@pytest.fixture
def session():
    engine = make_engine("sqlite:///:memory:")
    with make_session_factory(engine)() as s:
        cargar_datos(s)
        yield s
    engine.dispose()


@pytest.fixture
def client():
    with TestClient(crear_app("sqlite:///:memory:", seed=True)) as c:
        yield c
