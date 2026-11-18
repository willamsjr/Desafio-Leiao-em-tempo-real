# ADR-002 — PostgreSQL e bloqueio transacional para concorrência

**Status:** Aceita e implementada.

## Contexto

Duas pessoas podem enviar lances para o mesmo item simultaneamente. Sem coordenação, ambas poderiam validar seus valores contra um estado antigo e registrar resultados inconsistentes.

## Alternativas consideradas

- **Validação apenas no frontend:** insuficiente, pois os clientes têm estados diferentes e não são autoridade confiável.
- **Controle somente em memória no FastAPI:** depende de uma instância única e não oferece o mesmo controle transacional do banco.
- **Transação PostgreSQL com bloqueio de linha:** organiza o acesso concorrente ao mesmo item e permite validar/gravar o lance dentro da transação.

## Decisão

Usar o PostgreSQL e a operação de bloqueio de linha equivalente a `SELECT ... FOR UPDATE` ao processar lances para um mesmo item.

## Justificativa

A transação que obtém o bloqueio primeiro lê o estado vigente, valida o lance e confirma a atualização. A segunda aguarda; quando prossegue, encontra o estado alterado e rejeita o mesmo valor, porque não é superior ao lance atual.

## Consequências

- A **ordem de processamento no servidor/banco**, e não o horário de clique no navegador, determina qual lance igual é aceito.
- Os testes isolados não substituem o teste real de concorrência com PostgreSQL, que depende de `TEST_DATABASE_URL`.
- Uma restrição adicional `UNIQUE(item_id, valor)` **não integra a implementação atual**. É uma possível defesa complementar, não algo a declarar como existente.
- A lógica continua responsável por validar mínimo, lance anterior, prazo e anti-sniping sob a mesma coordenação transacional.
