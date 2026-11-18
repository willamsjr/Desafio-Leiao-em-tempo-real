from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.services import leilao_service


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
        with TestClient(app) as cliente:
            yield cliente
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def cadastrar(client: TestClient, fim: datetime, minimo: str = "100.00") -> int:
    resposta = client.post(
        "/itens", json={"nome": "Notebook", "lance_minimo": minimo, "encerra_em": fim.isoformat()}
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


def ofertar(client: TestClient, item_id: int, valor: str, participante="Ana"):
    return client.post(
        f"/itens/{item_id}/lances", json={"valor": valor, "participante": participante}
    )


def test_primeiro_lance_aceita_o_minimo_e_salva_historico(client):
    item_id = cadastrar(client, datetime.now(timezone.utc) + timedelta(hours=1))
    resposta = ofertar(client, item_id, "100.00")
    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["prorrogado"] is False
    assert resposta.json()["item"]["lance_atual"] == "100.00"
    historico = client.get(f"/itens/{item_id}/lances").json()
    assert len(historico) == 1
    assert historico[0]["participante"] == "Ana"
    assert historico[0]["valor"] == "100.00"


def test_rejeita_valor_inferior_ao_minimo_e_empate(client):
    item_id = cadastrar(client, datetime.now(timezone.utc) + timedelta(hours=1))
    assert ofertar(client, item_id, "99.99").status_code == 409
    assert ofertar(client, item_id, "110.00").status_code == 201
    assert ofertar(client, item_id, "110.00", "Beto").status_code == 409
    assert ofertar(client, item_id, "109.99", "Beto").status_code == 409
    assert len(client.get(f"/itens/{item_id}/lances").json()) == 1


def test_prorroga_exatamente_dois_minutos_no_ultimo_minuto(client, monkeypatch):
    agora = datetime.now(timezone.utc).replace(microsecond=0)
    original = agora + timedelta(minutes=1)
    item_id = cadastrar(client, original)
    monkeypatch.setattr(leilao_service, "agora_utc", lambda: agora)
    resultado = ofertar(client, item_id, "150.00")
    assert resultado.status_code == 201, resultado.text
    assert resultado.json()["prorrogado"] is True
    assert datetime.fromisoformat(resultado.json()["item"]["encerra_em"]).replace(
        tzinfo=timezone.utc
    ) == original + timedelta(minutes=2)


def test_prorroga_novamente_se_houver_outro_lance_na_nova_janela(client, monkeypatch):
    agora = datetime.now(timezone.utc).replace(microsecond=0)
    original = agora + timedelta(minutes=1)
    item_id = cadastrar(client, original)
    monkeypatch.setattr(leilao_service, "agora_utc", lambda: agora)
    assert ofertar(client, item_id, "100.00").json()["prorrogado"] is True
    monkeypatch.setattr(leilao_service, "agora_utc", lambda: agora + timedelta(minutes=2))
    segundo = ofertar(client, item_id, "110.00", "Beto")
    assert segundo.status_code == 201
    assert segundo.json()["prorrogado"] is True
    fim = datetime.fromisoformat(segundo.json()["item"]["encerra_em"])
    assert fim.replace(tzinfo=timezone.utc) == original + timedelta(minutes=4)


def test_nao_prorroga_fora_da_janela(client, monkeypatch):
    agora = datetime.now(timezone.utc).replace(microsecond=0)
    original = agora + timedelta(minutes=2, seconds=1)
    item_id = cadastrar(client, original)
    monkeypatch.setattr(leilao_service, "agora_utc", lambda: agora)
    resposta = ofertar(client, item_id, "100.00")
    assert resposta.status_code == 201
    assert resposta.json()["prorrogado"] is False


def test_rejeita_lance_apos_encerramento(client, monkeypatch):
    agora = datetime.now(timezone.utc).replace(microsecond=0)
    original = agora + timedelta(minutes=5)
    item_id = cadastrar(client, original)
    monkeypatch.setattr(leilao_service, "agora_utc", lambda: original)
    assert ofertar(client, item_id, "100.00").status_code == 409
    assert client.get(f"/itens/{item_id}/lances").json() == []


def test_websocket_recebe_o_lance_em_tres_abas(client):
    fim = datetime.now(timezone.utc) + timedelta(hours=1)
    item_id = cadastrar(client, fim)
    with client.websocket_connect(f"/ws/itens/{item_id}") as aba1:
        with client.websocket_connect(f"/ws/itens/{item_id}") as aba2:
            with client.websocket_connect(f"/ws/itens/{item_id}") as aba3:
                assert aba1.receive_json()["tipo"] == "conectado"
                assert aba2.receive_json()["tipo"] == "conectado"
                assert aba3.receive_json()["tipo"] == "conectado"
                resp = ofertar(client, item_id, "125.00")
                assert resp.status_code == 201, resp.text
                assert aba1.receive_json()["lance"]["valor"] == "125.00"
                assert aba2.receive_json()["item"]["lance_atual"] == "125.00"
                assert aba3.receive_json()["tipo"] == "novo_lance"


def test_item_inexistente_erro_404(client):
    assert ofertar(client, 999, "100.00").status_code == 404
    assert client.get('/itens/999/lances').status_code == 404


def test_prorroga_no_limite_exato_de_dois_minutos(client, monkeypatch):
    agora = datetime.now(timezone.utc).replace(microsecond=0)
    item_id = cadastrar(client, agora + timedelta(minutes=2))
    monkeypatch.setattr(leilao_service, "agora_utc", lambda: agora)
    assert ofertar(client, item_id, "100.00").json()["prorrogado"] is True
