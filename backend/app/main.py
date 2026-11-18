from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import models  # noqa: F401 - registra as tabelas no metadata
from app.controllers.item_controller import router as item_router
from app.controllers.lance_controller import router as lance_router
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Criacao automatica das tabelas para o prototipo academico.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Leilao em Tempo Real", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(item_router)
app.include_router(lance_router)


@app.get("/health", tags=["Saude"])
def health():
    return {"status": "ok"}


@app.get("/health/db", tags=["Saude"])
def health_db():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"database": "ok"}
