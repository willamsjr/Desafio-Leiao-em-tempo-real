from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect


class GerenciadorSalas:
    """Conexoes em memoria: uma unica instancia do FastAPI (sem Redis)."""

    def __init__(self):
        self.salas: dict[int, set[WebSocket]] = defaultdict(set)

    async def conectar(self, item_id: int, socket: WebSocket) -> None:
        await socket.accept()
        self.salas[item_id].add(socket)

    def desconectar(self, item_id: int, socket: WebSocket) -> None:
        self.salas[item_id].discard(socket)
        if not self.salas[item_id]:
            self.salas.pop(item_id, None)

    async def transmitir(self, item_id: int, mensagem: dict) -> None:
        for socket in list(self.salas.get(item_id, ())):
            try:
                await socket.send_json(mensagem)
            except (WebSocketDisconnect, RuntimeError, OSError):
                self.desconectar(item_id, socket)


gerenciador = GerenciadorSalas()
