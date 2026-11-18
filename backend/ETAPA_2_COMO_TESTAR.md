# Etapa 2 - Lances em tempo real (backend)

Projeto: FastAPI + PostgreSQL + SQLAlchemy + WebSocket. **Uma unica instancia** do FastAPI, sem Redis.

## Atualizar sem perder o banco

1. Guarde uma copia do seu `backend` atual.
2. Copie os arquivos deste ZIP por cima do `backend` existente, preservando **seu `.env`**.
3. Confira que `backend/.env` aponta para sua instalacao local de PostgreSQL (no seu computador, porta 5432).
4. Execute os comandos na pasta `backend` do Git Bash:

```bash
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

No PowerShell, use `\.venv\Scripts\python.exe` em lugar de `./.venv/Scripts/python.exe`.

## Rotas

- `POST /itens` e `GET /itens`: cadastro e listagem existentes, **preservados**.
- `GET /itens/{id}`: estado oficial do item.
- `POST /itens/{id}/lances`: lance, com corpo `{"participante":"Ana","valor":"1100.00"}`.
- `GET /itens/{id}/lances`: historico ordenado do mais antigo para o mais novo.
- `WS /ws/itens/{id}`: sala de notificacoes em tempo real. Primeiro evento: `{"tipo":"conectado","item_id":1}`. Apos um lance aceito: `{"tipo":"novo_lance", "lance": {...}, "item": {...}, "prorrogado": false}`.

`POST` retorna HTTP **201** se aceitar. Valor menor que o minimo, empate, lance apos encerramento e demais conflitos retornam **409**. ID inexistente retorna **404**.

**Anti-sniping:** quando um lance valido for recebido faltando **ate 2 minutos**, o encerramento e prorrogado **2 minutos a partir do prazo anterior**. Novos lances durante uma nova janela final provocam novas prorrogacoes. O horario e calculado no servidor **apos adquirir o bloqueio da linha**.

**Concorrencia:** `SELECT ... FOR UPDATE` (PostgreSQL) bloqueia a linha do item durante a transacao. Dois lances iguais enviados simultaneamente nao serao ambos aceitos.

**Reconexao:** quando o WebSocket abrir ou reconectar, o React deve refazer `GET /itens/{id}` e `GET /itens/{id}/lances` para obter o estado oficial.

## Testes

```bash
./.venv/Scripts/python.exe -m pytest -q
```

A maioria dos testes usa SQLite apenas para velocidade e isolamento. **O teste de concorrencia real usa PostgreSQL** e e ativado ao definir a variavel `TEST_DATABASE_URL`, em Git Bash:

```bash
export TEST_DATABASE_URL='postgresql+psycopg://leilao:leilao_dev@localhost:5432/leilao_db'
./.venv/Scripts/python.exe -m pytest -q
```

Esse teste cria um schema de teste temporario com nome aleatorio e o apaga ao final; requer permissao do usuario de banco para criar schema. Nao executa alteracoes nas tabelas reais do leilao.

> **Seguranca:** credenciais sao so para desenvolvimento local. Nao publique seu `.env`. O ZIP nao inclui o `.env` original nem a `.venv` Windows, que deve ser mantida no computador.

## Limites da versao academica

- A transmissao WebSocket funciona com um processo FastAPI (sem Redis / multiplos workers).
- O PostgreSQL decide a concorrencia; SQLite nao comprova esse comportamento.
- Se o servidor cair entre COMMIT e notificacao, o lance persiste e o navegador deve recuperar o estado via GET na reconexao.
- Sem autenticacao: o nome do participante e apenas um identificador de demonstracao.
- A interface React ainda nao faz parte deste ZIP do backend.
