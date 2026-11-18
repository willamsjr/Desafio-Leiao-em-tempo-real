from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.item import ItemCreate, ItemRead
from app.services import item_service

router = APIRouter(prefix="/itens", tags=["Itens"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def cadastrar_item(dados: ItemCreate, db: DbSession):
    return item_service.cadastrar_item(db, dados)


@router.get("", response_model=list[ItemRead])
def listar_itens(db: DbSession):
    return item_service.listar_itens(db)


@router.get("/{item_id}", response_model=ItemRead)
def buscar_item(item_id: int, db: DbSession):
    return item_service.buscar_item(db, item_id)
