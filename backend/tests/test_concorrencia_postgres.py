"""Teste de concorrencia real. Requer TEST_DATABASE_URL apontando para PostgreSQL.

Nao afeta as tabelas existentes: cria e remove um schema de teste exclusivo.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Item, Lance
from app.schemas.lance import LanceCreate
from app.services.leilao_service import registrar_lance


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Defina TEST_DATABASE_URL para teste real PostgreSQL")
def test_dois_lances_iguais_simultaneos_postgresql():
    url = os.environ["TEST_DATABASE_URL"]
    assert url.startswith("postgresql+psycopg://"), "O teste requer PostgreSQL"
    schema = "teste_leilao_" + uuid4().hex[:12]
    admin_engine = create_engine(url)
    isolation_engine = None
    try:
        with admin_engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        isolation_engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
        Base.metadata.create_all(isolation_engine)
        with Session(isolation_engine) as db:
            item = Item(
                nome="Concorrencia",
                lance_minimo=Decimal("100.00"),
                encerra_em=datetime.now(timezone.utc) + timedelta(hours=1),
            )
            db.add(item)
            db.commit()
            item_id = item.id

        barreira = Barrier(2)

        def tentar(participante: str) -> int:
            with Session(isolation_engine) as db:
                barreira.wait(timeout=10)
                try:
                    registrar_lance(
                        db, item_id,
                        LanceCreate(participante=participante, valor=Decimal("150.00")),
                    )
                except HTTPException as erro:
                    return erro.status_code
                return 201

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(tentar, nome) for nome in ("Ana", "Beto")]
            resultados = [f.result(timeout=20) for f in futures]

        assert sorted(resultados) == [201, 409]
        with Session(isolation_engine) as db:
            assert db.scalar(select(func.count()).select_from(Lance)) == 1
            assert db.get(Item, item_id).lance_atual == Decimal("150.00")
    finally:
        if isolation_engine is not None:
            isolation_engine.dispose()
        with admin_engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin_engine.dispose()
