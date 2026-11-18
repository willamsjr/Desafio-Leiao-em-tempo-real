from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.database import get_db
from app.schemas.lance import LanceCreate, LanceRead, LanceResultado
from app.services import leilao_service
from app.websocket import gerenciador

router = APIRouter(tags=["Lances"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/itens/{item_id}/lances",
    response_model=LanceResultado,
    status_code=status.HTTP_201_CREATED,
)
async def oferecer_lance(item_id: int, dados: LanceCreate, db: DbSession):
    # O banco sincrono roda em um worker, sem bloquear o event loop do WebSocket.
    resultado = await run_in_threadpool(
        leilao_service.registrar_lance, db, item_id, dados
    )
    # A transmissao acontece apenas depois do COMMIT bem-sucedido.
    await gerenciador.transmitir(
        item_id, {"tipo": "novo_lance", **resultado.model_dump(mode="json")}
    )
    return resultado


@router.get("/itens/{item_id}/lances", response_model=list[LanceRead])
def historico_lances(item_id: int, db: DbSession):
    return leilao_service.listar_lances(db, item_id)


@router.websocket("/ws/itens/{item_id}")
async def sala_leilao(socket: WebSocket, item_id: int):
    await gerenciador.conectar(item_id, socket)
    try:
        await socket.send_json(
            {
                "tipo": "conectado",
                "item_id": item_id,
                "agora": leilao_service.agora_utc().isoformat(),
            }
        )
        # O cliente consulta GET /itens/{id} e GET /itens/{id}/lances
        # ao entrar e apos reconectar, evitando perda de eventos.
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        gerenciador.desconectar(item_id, socket)
