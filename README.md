# Leilão em Tempo Real

**Disciplina:** Programação Avançada  
**Projeto:** plataforma acadêmica de leilão com comunicação em tempo real.

## 1. Visão geral

O sistema permite cadastrar itens com lance mínimo e horário de encerramento, visualizar os leilões disponíveis e entrar na sala de um item. Na sala, o participante acompanha o maior lance, o histórico e o tempo restante, além de enviar novos lances.

As atualizações são distribuídas por **WebSocket**, sem precisar recarregar a página. Se um lance válido chegar nos **últimos 2 minutos**, o sistema acrescenta **2 minutos ao horário de encerramento** (*anti-sniping*).

**Escopo:** protótipo acadêmico, com uma instância do FastAPI. Não há login ou pagamentos; os participantes informam um nome para a demonstração. Redis Pub/Sub não é necessário nessa configuração.

## 2. Tecnologias

| Camada | Tecnologias |
| --- | --- |
| Backend | Python 3.11+ e FastAPI |
| Frontend | React, Vite e CSS |
| Banco de dados | PostgreSQL e SQLAlchemy |
| Tempo real | WebSocket do FastAPI |
| Testes | Pytest (SQLite nos testes isolados e PostgreSQL no teste real de concorrência) |
| Serviço adicional | PostgreSQL por Docker Compose, **ou** PostgreSQL instalado localmente |

## 3. Estrutura e arquitetura

Arquitetura **MVC adaptada**, com camada de serviços:

- **Model:** modelos SQLAlchemy e persistência no PostgreSQL.
- **View:** interface React (listagem e sala do leilão).
- **Controller:** rotas HTTP e WebSocket no FastAPI.
- **Services:** validação dos lances, controle de concorrência e anti-sniping.

```text
leilao/
├── backend/
│   ├── app/
│   │   ├── controllers/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── database.py
│   │   ├── main.py
│   │   └── websocket.py
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 4. Preparar o PostgreSQL

**Escolha uma das opções abaixo.** Não é necessário executar as duas.

### Opção A — Docker Compose (Windows ou macOS)

Instale Docker Desktop e inicie o mecanismo do Docker. Na pasta raiz do projeto (`leilao/`), execute:

```bash
docker compose up -d --wait
```

O `docker-compose.yml` fornecido usa **porta 5433 no computador**, direcionada à porta 5432 dentro do contêiner. Na pasta `backend/`, crie `.env` com:

```env
DATABASE_URL=postgresql+psycopg://leilao:leilao_dev@localhost:5433/leilao_db
```

> As credenciais acima servem **somente para desenvolvimento local**. Nunca publique o arquivo `.env`.

### Opção B — PostgreSQL instalado diretamente no Windows

Esta foi a alternativa utilizada durante o desenvolvimento, porque o Docker Desktop apresentou um problema de inicialização nessa máquina. Configure o PostgreSQL na porta **5432** e crie o usuário e o banco (uma única vez), no `SQL Shell (psql)` conectado como `postgres`:

```sql
CREATE ROLE leilao WITH LOGIN PASSWORD 'leilao_dev';
CREATE DATABASE leilao_db OWNER leilao;
```

Na pasta `backend/`, crie `.env` com:

```env
DATABASE_URL=postgresql+psycopg://leilao:leilao_dev@localhost:5432/leilao_db
```

Se o usuário e o banco já existirem, **não repita** os comandos SQL. O arquivo `backend/.env.example` deve servir como referência; ajuste a porta conforme sua instalação. O código cria as tabelas automaticamente ao iniciar, para simplificar o protótipo.

## 5. Executar no Windows

É necessário ter **Python 3.11 ou superior** e **Node.js com npm**, além do PostgreSQL da seção anterior.

### Backend — Git Bash (usado no desenvolvimento)

Na pasta `leilao/`:

```bash
cd backend
py -3 -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

Se `.venv` já existir, não é necessário recriá-lo. Antes de iniciar, confirme que `backend/.env` foi criado para a opção de banco escolhida.

**Alternativa PowerShell**, dentro de `backend/`:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Frontend — outro terminal

Na pasta raiz `leilao/`:

```bash
cd frontend
npm install
npm run dev
```

**Endereços:** frontend <http://localhost:5173>, API/Swagger <http://127.0.0.1:8000/docs>, verificação do banco <http://127.0.0.1:8000/health/db>.

## 6. Executar no macOS

É necessário ter Python 3.11+, Node.js/npm e Docker Desktop, ou uma instalação local compatível do PostgreSQL.

No Terminal, na pasta raiz `leilao/`, execute `docker compose up -d --wait` se usar a **Opção A**. Crie `backend/.env` com a URL da porta **5433**, conforme descrito acima.

**Terminal 1 — backend:**

```bash
cd backend
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — frontend** (partindo da raiz do projeto):

```bash
cd frontend
npm install
npm run dev
```

Acesse <http://localhost:5173>. Para usar PostgreSQL local no Mac, ajuste a `DATABASE_URL` à porta e às credenciais correspondentes.

## 7. Rotas da API

| Método | Caminho | Finalidade |
| --- | --- | --- |
| `GET` | `/health` | Saúde da API |
| `GET` | `/health/db` | Teste de conexão com o banco |
| `POST` | `/itens` | Cadastro de item |
| `GET` | `/itens` | Listagem de itens |
| `GET` | `/itens/{item_id}` | Dados atuais do item |
| `POST` | `/itens/{item_id}/lances` | Registrar novo lance |
| `GET` | `/itens/{item_id}/lances` | Histórico de lances |
| WebSocket | `/ws/itens/{item_id}` | Eventos em tempo real da sala |

Exemplo de novo lance (`POST /itens/1/lances`):

```json
{"participante":"Ana","valor":"1100.00"}
```

O cadastro de leilões pode ser realizado diretamente pela interface React ou pela documentação interativa do FastAPI (Swagger).

## 8. Regras e decisões técnicas

### Por que WebSocket em vez de polling?

No **polling**, cada navegador solicita atualizações em intervalos fixos, mesmo quando não há lance novo. Isso gera requisições desnecessárias e o lance pode aparecer apenas na consulta seguinte. Com **WebSocket**, a conexão permanece aberta e o servidor comunica as mudanças aos participantes conectados assim que elas ocorrem.

Nesta implementação, o navegador **envia** o lance por `POST` HTTP; após validar e confirmar o registro no banco, o FastAPI **distribui** o evento `novo_lance` por WebSocket. Assim a sala atualiza lance atual, histórico e horário de encerramento sem recarregar.

### Dois lances iguais no mesmo instante

A decisão cabe ao **servidor**, apoiado no controle transacional do **PostgreSQL**. O serviço bloqueia a linha do item com `SELECT ... FOR UPDATE`, consulta o maior lance e valida a oferta dentro de uma transação. Se dois participantes oferecerem o mesmo valor, **um poderá ser aceito e o outro será rejeitado** porque o valor já não supera o lance atual. A ordem efetiva de obtenção do bloqueio determina qual transação é processada primeiro; o cliente não decide o vencedor.

### Anti-sniping

O servidor verifica o horário depois de obter o bloqueio do item. Se um lance **válido** chegar quando faltam **mais de 0 e até 2 minutos**, acrescenta **2 minutos ao encerramento anterior**. Outros lances válidos que ocorrerem novamente na janela final podem prorrogar o leilão mais vezes. Lances após o encerramento não são aceitos.

### Limites da versão

- A distribuição WebSocket usa conexões em memória e **uma instância** do FastAPI. Redis Pub/Sub seria uma evolução para múltiplas instâncias.

- O cronômetro do React é sincronizado com o relógio do servidor ao estabelecer a conexão WebSocket.

- O servidor continua sendo a autoridade responsável por validar o prazo de encerramento.

- O protótipo não possui autenticação nem pagamentos. Durante uma desconexão, eventos WebSocket podem ser perdidos, mas o frontend recupera o estado do leilão e o histórico de lances por consultas HTTP ao reconectar.

- Os registros de leilões encerrados são mantidos; a exclusão automática não foi implementada.


### Reconexão e sincronização

O frontend realiza reconexão automática do WebSocket
quando a conexão é interrompida.

Ao estabelecer ou restabelecer a conexão, o React
consulta a API para atualizar os dados do leilão
e recuperar o histórico de lances.

Os lances recebidos são mesclados pelo ID,
evitando duplicações e atualizações fora de ordem.

O WebSocket não armazena nem reenvia eventos antigos.
A recuperação acontece por meio das consultas HTTP.

A interface também apresenta o estado da conexão:
"Conectado em tempo real" ou "Reconectando...".

## 9. Testes automatizados

Os testes cobrem cadastro, validação de lances, anti-sniping, histórico e comunicação. O teste de concorrência com PostgreSQL é opcional na configuração padrão e depende de `TEST_DATABASE_URL`.

**Windows (Git Bash), dentro de `backend/`:**

```bash
./.venv/Scripts/python.exe -m pytest -rs -q
```

**macOS, dentro de `backend/`:**

```bash
./.venv/bin/python -m pytest -rs -q
```

Para **ativar o teste real de concorrência PostgreSQL**, aponte `TEST_DATABASE_URL` para seu banco de desenvolvimento. No **Git Bash ou macOS**:

```bash
export TEST_DATABASE_URL="$(sed -n 's/^DATABASE_URL=//p' .env | tr -d '\r')"
```

No **PowerShell**:

```powershell
$env:TEST_DATABASE_URL = ((Get-Content .env | Where-Object { $_ -match '^DATABASE_URL=' }) -replace '^DATABASE_URL=', '')
```

Em seguida, execute o Pytest novamente. O teste real cria e apaga um **schema temporário** no PostgreSQL; exige que o usuário do banco tenha permissão para isso.

**Resultado obtido durante o desenvolvimento no Windows:** `14 passed, 1 warning`. Isso é um registro do teste realizado, não uma garantia sobre outras instalações.

## 10. Demonstração para o professor

1. Iniciar o backend FastAPI e o frontend React.

2. Cadastrar um leilão pelo formulário React, definindo lance mínimo e horário de encerramento próximo.

3. Abrir a sala do mesmo leilão em três navegadores diferentes.

4. Registrar lances e demonstrar que o lance atual e o histórico são atualizados automaticamente nos três navegadores, sem recarregar a página.

5. Realizar um lance válido quando faltar menos de 1 minuto e demonstrar a prorrogação automática de 2 minutos (anti-sniping).

6. Apresentar os resultados dos testes Pytest, incluindo o teste de concorrência no PostgreSQL, e explicar como o servidor decide entre lances simultâneos.

## 11. Cuidados com o repositório

- Não versionar `.env`, `.venv/`, `node_modules/` nem arquivos locais de banco.
- O arquivo `.env.example` pode ser versionado como exemplo, sem credenciais de produção.
- O Docker Compose foi fornecido para executar PostgreSQL, mas o desenvolvimento também ocorreu com PostgreSQL local no Windows.
