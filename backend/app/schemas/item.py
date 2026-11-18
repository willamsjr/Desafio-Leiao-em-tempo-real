from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ItemCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    lance_minimo: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    encerra_em: datetime

    @field_validator("encerra_em")
    @classmethod
    def exigir_fuso_horario(cls, valor: datetime) -> datetime:
        if valor.tzinfo is None or valor.utcoffset() is None:
            raise ValueError("Informe encerra_em com fuso horario, por exemplo -03:00")
        return valor


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    lance_minimo: Decimal
    lance_atual: Decimal | None
    encerra_em: datetime
