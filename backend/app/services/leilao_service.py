from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item, Lance
from app.schemas.lance import LanceCreate, LanceResultado


JANELA_ANTI_SNIPING = timedelta(minutes=2)
PRORROGACAO = timedelta(minutes=2)


def agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _utc(horario: datetime) -> datetime:
    # PostgreSQL respeita o fuso em DateTime(timezone=True).
    # SQLite (usado apenas em testes unitarios) devolve UTC sem tzinfo.
    if horario.tzinfo is None:
        return horario.replace(tzinfo=timezone.utc)
    return horario.astimezone(timezone.utc)


def registrar_lance(db: Session, item_id: int, dados: LanceCreate) -> LanceResultado:
    # No PostgreSQL, FOR UPDATE bloqueia a linha ate o fim da transacao.
    # Assim dois valores iguais nunca sao aceitos ao mesmo tempo.
    with db.begin():
        item = db.execute(
            select(Item).where(Item.id == item_id).with_for_update(of=Item)
        ).scalar_one_or_none()
        if item is None:
            raise HTTPException(status_code=404, detail="Item nao encontrado")

        # O horario so e consultado DEPOIS de adquirir o bloqueio.
        agora = agora_utc()
        encerramento = _utc(item.encerra_em)
        if agora >= encerramento:
            raise HTTPException(status_code=409, detail="O leilao ja encerrou")

        if item.lance_atual is None:
            if dados.valor < item.lance_minimo:
                raise HTTPException(
                    status_code=409,
                    detail="O primeiro lance deve ser igual ou maior que o lance minimo",
                )
        elif dados.valor <= item.lance_atual:
            raise HTTPException(
                status_code=409, detail="O novo lance deve superar o lance atual"
            )

        participante = dados.participante.strip()
        if not participante:
            raise HTTPException(status_code=422, detail="Informe o participante")

        lance = Lance(item_id=item_id, participante=participante, valor=dados.valor)
        db.add(lance)
        item.lance_atual = dados.valor

        restante = encerramento - agora
        prorrogado = timedelta(0) < restante <= JANELA_ANTI_SNIPING
        if prorrogado:
            # Acrescenta 2 minutos ao prazo, nao ao horario do lance.
            item.encerra_em = encerramento + PRORROGACAO

        db.flush()
        # O COMMIT ocorre ao sair do bloco. Nada e transmitido antes dele.

    # Os valores serao serializados pelo Pydantic apos o commit.
    return LanceResultado(
        lance=lance,
        item=item,
        prorrogado=prorrogado,
    )


def listar_lances(db: Session, item_id: int) -> list[Lance]:
    if db.get(Item, item_id) is None:
        raise HTTPException(status_code=404, detail="Item nao encontrado")
    return list(
        db.scalars(
            select(Lance)
            .where(Lance.item_id == item_id)
            .order_by(Lance.id.asc())
        ).all()
    )
