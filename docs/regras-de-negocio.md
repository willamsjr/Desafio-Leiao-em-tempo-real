# Especificação — Regras de negócio do leilão

**Status:** regras implementadas no protótipo acadêmico.

## RN-01 — Cadastro de itens

- Um item possui nome, lance mínimo e horário fixado para encerramento.
- O servidor valida os dados recebidos; o encerramento cadastrado deve estar no futuro.
- Após cadastro confirmado, o item aparece na listagem e pode ter sua sala aberta.

## RN-02 — Validade do lance

- O participante informa seu nome e o valor do lance.
- O lance deve respeitar o mínimo do item e superar o lance atual, se houver.
- O leilão deve estar aberto no momento da validação pelo servidor.
- Lances inválidos devem ser rejeitados; não se deve confiar somente nas validações do formulário.
- O envio de um lance ocorre por HTTP, e a atualização aos participantes conectados ocorre por WebSocket após a confirmação da transação.

## RN-03 — Dois lances simultâneos

**Cenário:** duas pessoas enviam lances iguais ao mesmo item, praticamente no mesmo instante.

1. Cada requisição tenta obter o bloqueio transacional do registro do item no PostgreSQL.
2. Uma transação obtém o bloqueio e valida o lance frente ao valor atual.
3. A outra aguarda e depois verifica o estado atualizado.
4. Se o valor já não supera o lance atual, o segundo lance é rejeitado.

**Resultado esperado:** para dois lances iguais concorrentes sobre o mesmo estado, no máximo um é aceito. A ordem depende da obtenção do bloqueio, não do horário informado pelo navegador.

## RN-04 — Anti-sniping

- Se um lance válido for aceito quando faltam **mais de zero e até dois minutos** para encerrar, o sistema soma **dois minutos ao horário de encerramento anterior**.
- Se faltavam 40 segundos, passam a faltar aproximadamente 2 minutos e 40 segundos.
- Um novo lance válido na janela final pode provocar outra prorrogação.
- Não há limite de prorrogações definido nesta versão.
- Lances feitos após o encerramento são rejeitados.

## RN-05 — Atualização em tempo real

- A sala apresenta o maior lance, o histórico, o encerramento e o tempo restante.
- Quando o servidor confirma um lance, envia `novo_lance` por WebSocket aos clientes da sala.
- A interface atualiza o estado sem exigir F5.
- O histórico é mesclado pelos IDs para evitar duplicações.

## RN-06 — Desconexão e relógio

- O React indica o estado da conexão e tenta reconectar após queda do WebSocket.
- A reconexão provoca consultas HTTP para sincronizar os dados e o histórico perdidos enquanto a conexão estava indisponível.
- O evento `conectado` envia um horário do servidor para ajuste do relógio visual do React.
- **A aceitação do lance e o prazo são decididos pelo servidor**, mesmo quando a máquina do participante tem horário incorreto.

## Verificações de aceitação

- Cadastrar um item no React e confirmar que ele permanece após F5.
- Abrir o mesmo leilão em três navegadores e confirmar que um novo lance aparece nos três, inclusive no histórico.
- Enviar lances iguais simultaneamente e confirmar que somente um é aceito, usando o teste de concorrência com PostgreSQL.
- Enviar lance válido nos dois minutos finais e confirmar a prorrogação de dois minutos.
- Desligar/religar o backend e confirmar que a interface volta a sincronizar sem F5.
- Reiniciar o contêiner PostgreSQL e confirmar que os dados persistem no volume.

## Fora do escopo

Não foram implementados login, pagamento, limite de prorrogações, emissão de evento específico de vencedor, Redis Pub/Sub ou exclusão automática de itens encerrados.
