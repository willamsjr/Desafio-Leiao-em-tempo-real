from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.item import ItemRead


class LanceCreate(BaseModel):
    participante: str = Field(min_length=1, max_length=80)
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class LanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    participante: str
    valor: Decimal
    criado_em: datetime


class LanceResultado(BaseModel):
    lance: LanceRead
    item: ItemRead
    prorrogado: bool
