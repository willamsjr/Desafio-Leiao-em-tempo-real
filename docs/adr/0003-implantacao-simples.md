# ADR-003 — Instância única FastAPI e PostgreSQL via Docker Compose

**Status:** Aceita e implementada.

## Contexto

O projeto tem escopo acadêmico e precisa ser demonstrável em diferentes computadores sem introduzir serviços distribuídos desnecessários.

## Alternativas consideradas

- PostgreSQL instalado manualmente no computador.
- PostgreSQL executado em contêiner Docker.
- Várias instâncias FastAPI com broker Redis Pub/Sub.

## Decisão

Fornecer `docker-compose.yml` para executar **apenas PostgreSQL 16**, com volume persistente. Executar FastAPI e React separadamente conforme o README. Manter **uma única instância FastAPI** com gerenciador de WebSocket em memória; não incluir Redis.

## Justificativa

O Compose padroniza a criação do banco e usuário locais em outros computadores. Para o volume e o prazo deste protótipo, uma instância FastAPI atende ao objetivo sem a complexidade de um broker de mensagens.

## Consequências

- Porta PostgreSQL no host: `5433` com Docker, ou `5432` na instalação local usada durante o desenvolvimento.
- `DATABASE_URL` deve refletir a opção escolhida. Arquivos `.env` não devem ser enviados ao GitHub.
- Dados do banco em contêiner persistem no volume nomeado `postgres_data` ao reiniciar o contêiner.
- Não afirmar que `docker compose up` inicia o sistema inteiro: ele inicia somente o banco.
- Múltiplas instâncias FastAPI exigiriam outra forma de distribuir eventos entre processos; Redis Pub/Sub é uma alternativa futura, não uma funcionalidade atual.
