# ADR-001 — HTTP para operações e WebSocket para atualizações

**Status:** Aceita e implementada.

## Contexto

Todos os participantes precisam visualizar lances e atualizações do encerramento sem recarregar a página. Precisávamos escolher como transportar operações e notificações.

## Alternativas consideradas

- **Polling:** simples, mas gera requisições repetidas mesmo quando não há lances e pode atrasar uma atualização até o próximo intervalo.
- **Long polling:** reduz requisições vazias, com gestão mais complexa de conexões/requisições.
- **SSE:** opção viável para notificações unidirecionais do servidor ao cliente.
- **WebSocket:** conexão persistente e bidirecional, apropriada a atualizações de salas em tempo real.

## Decisão

Manter **HTTP** para criar/consultar itens e enviar lances; usar **WebSocket** para distribuir o evento `novo_lance` aos participantes da sala após a confirmação no banco.

## Justificativa

Separar a operação HTTP da notificação permite respostas individuais com códigos de sucesso/erro e torna os testes mais diretos. O WebSocket elimina a necessidade de consultar repetidamente a sala para descobrir novos lances. Também atende ao requisito acadêmico explícito.

## Consequências e limitações

- É necessário gerenciar conexão, desconexão e reconexão.
- Mensagens enviadas durante a desconexão não são armazenadas pelo WebSocket; o frontend recompõe o estado por HTTP ao reconectar.
- Como nesta implementação o lance é enviado por HTTP, **SSE também poderia atender à parte de notificações**. A escolha por WebSocket não é baseada em exclusividade técnica.
- Eventos são distribuídos em memória por uma única instância FastAPI.
