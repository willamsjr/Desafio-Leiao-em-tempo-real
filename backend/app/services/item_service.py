from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item
from app.schemas.item import ItemCreate


def cadastrar_item(db: Session, dados: ItemCreate) -> Item:
    if dados.encerra_em <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="O encerramento deve estar no futuro")

    item = Item(
        nome=dados.nome.strip(),
        lance_minimo=dados.lance_minimo,
        encerra_em=dados.encerra_em,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def listar_itens(db: Session) -> list[Item]:
    return list(db.scalars(select(Item).order_by(Item.id.desc())).all())


def buscar_item(db: Session, item_id: int) -> Item:
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item nao encontrado")
    return item
