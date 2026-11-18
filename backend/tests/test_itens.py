from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def db_teste():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = db_teste
    try:
        # Nao inicia o lifespan: somente o banco de teste e usado.
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_cadastra_e_lista_item(client):
    fim = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    resposta = client.post(
        "/itens", json={"nome": "Notebook", "lance_minimo": "100.00", "encerra_em": fim}
    )
    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["nome"] == "Notebook"
    assert resposta.json()["lance_atual"] is None
    assert len(client.get("/itens").json()) == 1


def test_rejeita_encerramento_passado(client):
    passado = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    resposta = client.post(
        "/itens", json={"nome": "Notebook", "lance_minimo": "100.00", "encerra_em": passado}
    )
    assert resposta.status_code == 400


def test_rejeita_item_inexistente(client):
    assert client.get("/itens/999").status_code == 404
