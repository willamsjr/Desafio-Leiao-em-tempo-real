from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Item(Base):
    __tablename__ = "itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    lance_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    lance_atual: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    encerra_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    lances: Mapped[list["Lance"]] = relationship(back_populates="item")
