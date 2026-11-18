# Arquitetura — Leilão em Tempo Real

## Objetivo

Permitir cadastro e consulta de leilões, envio de lances concorrentes e atualização da sala em tempo real, com consistência garantida no servidor.

## Componentes

| Camada | Tecnologia | Responsabilidade |
| --- | --- | --- |
| View | React + Vite | Cadastro, cards, sala, cronômetro, envio de lances, estado de conexão e histórico |
| Controller | FastAPI | Rotas HTTP e endpoint WebSocket |
| Services | Python | Validação das regras, anti-sniping, transações e concorrência |
| Model | SQLAlchemy + PostgreSQL | Itens, lances, armazenamento persistente e bloqueios transacionais |
| Infraestrutura local | Docker Compose | Iniciar PostgreSQL em contêiner quando escolhido |

A organização é descrita como **MVC adaptado**, com uma camada explícita de serviços. React e FastAPI são processos separados.

## Fluxo de cadastro

1. O participante preenche o formulário no React.
2. O cliente realiza `POST /itens` com nome, lance mínimo e horário de encerramento.
3. O FastAPI valida e grava o item no PostgreSQL.
4. Após confirmação HTTP, a interface adiciona o item à lista. Uma nova consulta também permite recuperá-lo.

## Fluxo de um lance

```text
React (participante)
   | POST /itens/{id}/lances (HTTP)
   v
FastAPI controller
   |
   v
Service: transação + bloqueio do item + validações
   |
   v
PostgreSQL: registra lance e confirma transação
   |
   +--> Resposta HTTP ao participante que enviou
   |
   +--> Evento WebSocket "novo_lance" para a sala
                                     |
                                     v
                           React em outros navegadores
```

**Responsabilidades distintas:** HTTP envia comandos/consultas; WebSocket distribui mudanças para clientes conectados. O evento é divulgado após o commit. O cliente não escolhe qual lance vence.

## Estado e reconexão

- O cliente mantém a conexão WebSocket da sala selecionada.
- A sala recebe o evento `novo_lance`, com informações do item e do lance.
- O evento `conectado` informa o horário do servidor usado para ajustar o cronômetro visual.
- Se a conexão cair, o React tenta reconectar; ao abrir/reabrir, busca por HTTP os dados atuais e o histórico.
- O histórico é mesclado por ID para evitar duplicação; atualizações antigas não devem substituir o estado de um lance mais recente.
- Esta estratégia **recupera o estado**, não implica replay de eventos pelo WebSocket.

## Persistência e operação

- PostgreSQL é o banco oficial para o funcionamento do sistema.
- Em Windows, pode-se usar PostgreSQL instalado localmente (`5432`) ou PostgreSQL do Docker Compose (`5433` no host).
- O Compose atual contém **apenas** o serviço de banco de dados. FastAPI e React são iniciados separadamente.
- As conexões WebSocket são mantidas em memória numa única instância de FastAPI; não existe broker Redis nesta versão.

## Limites conhecidos

Protótipo acadêmico sem autenticação, pagamentos, distribuição multi-instância nem exclusão automática de leilões encerrados. O cronômetro da interface é informativo; o backend valida o prazo efetivo.
