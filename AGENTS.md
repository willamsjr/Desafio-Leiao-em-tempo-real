# AGENTS.md — Leilão em Tempo Real

## Objetivo deste arquivo

Orientar integrantes da equipe e ferramentas de assistência ao desenvolvimento sobre a arquitetura, as regras efetivamente implementadas e os limites do protótipo acadêmico. **Este arquivo é documentação, não uma configuração executável.**

## Contexto e estrutura

- `frontend/`: interface React + Vite; cadastro de itens, listagem, sala, histórico, cronômetro e conexão WebSocket.
- `backend/app/controllers/`: rotas HTTP e WebSocket do FastAPI.
- `backend/app/services/`: regras de negócio de itens e lances, concorrência e anti-sniping.
- `backend/app/models/` e `backend/app/schemas/`: persistência SQLAlchemy e contratos de entrada/saída.
- `backend/tests/`: testes automatizados, inclusive teste de concorrência com PostgreSQL.
- `docker-compose.yml`: inicializa **somente o PostgreSQL**, não o frontend e o backend.
- `docs/`: arquitetura, especificação das regras e registros das decisões (ADRs).

## Decisões de engenharia adotadas

1. Arquitetura **MVC adaptada**, com serviços separados dos controllers.
2. Operações de cadastro, consultas e envio de lances usam **HTTP**; o WebSocket distribui eventos aos participantes de uma sala.
3. A validação do lance e do prazo acontece **no servidor**, nunca por confiança no relógio ou nos dados do navegador.
4. O PostgreSQL utiliza **transações e bloqueio de linha (`SELECT ... FOR UPDATE`)** para processar lances concorrentes de um mesmo item.
5. O **anti-sniping** acrescenta dois minutos ao encerramento anterior quando um lance válido é aceito nos dois minutos finais, antes de o item encerrar.
6. O frontend reconecta o WebSocket em caso de queda e recupera o estado/histórico por **consultas HTTP**. O WebSocket não reenvia eventos perdidos.
7. O cronômetro visual é sincronizado ao relógio informado pelo FastAPI, mas a decisão de aceitar lances permanece no backend.
8. Uma única instância FastAPI: distribuição de eventos em memória. **Redis não faz parte desta versão.**

## Regras para alterações

- Não alterar as regras de lance mínimo, comparação com o lance atual, prazo final ou anti-sniping sem atualizar `docs/regras-de-negocio.md` e os testes correspondentes.
- Não mover a autoridade de validação de lances para o React.
- Não publicar eventos de lance antes da confirmação no banco de dados.
- Preservar a consistência sob concorrência; mudanças em transações/bloqueios exigem teste real com PostgreSQL.
- Não adicionar login, pagamentos, Redis, exclusão automática, limites de prorrogação ou outros requisitos não solicitados e não implementados.
- Não documentar como implementado aquilo que for apenas uma proposta.
- Não versionar `.env`, `.venv/`, `node_modules/`, caches ou dados locais do banco.
- Alterações funcionais devem ser verificadas com os testes e, quando aplicável, com dois ou três navegadores.

## Execução e verificação

Consulte o `README.md` da raiz para instalação no Windows/macOS e as alternativas de PostgreSQL.

- API: `http://127.0.0.1:8000`.
- Frontend: `http://localhost:5173`.
- PostgreSQL local: porta `5432`; via Docker Compose: porta `5433` no computador.
- Testes: executar `pytest -rs -q` em `backend/`. Para incluir o teste de concorrência real, definir `TEST_DATABASE_URL` apontando para um PostgreSQL de testes com as permissões necessárias.

## Documentos relacionados

- [`docs/arquitetura.md`](docs/arquitetura.md) — componentes e fluxo cliente-servidor.
- [`docs/regras-de-negocio.md`](docs/regras-de-negocio.md) — especificação das regras.
- [`docs/adr/0001-comunicacao-http-websocket.md`](docs/adr/0001-comunicacao-http-websocket.md) — decisão sobre HTTP e WebSocket.
- [`docs/adr/0002-postgresql-concorrencia.md`](docs/adr/0002-postgresql-concorrencia.md) — decisão sobre banco e concorrência.
- [`docs/adr/0003-implantacao-simples.md`](docs/adr/0003-implantacao-simples.md) — Docker Compose, instância única e Redis.
