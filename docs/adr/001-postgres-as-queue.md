# ADR 001: PostgreSQL como Fila de Mensagens

## Status
Proposto

## Contexto
Precisamos de um sistema de mensageria para processar tarefas assíncronas. Tradicionalmente, seriam usados Redis (BullMQ) ou RabbitMQ. No entanto, essas tecnologias introduzem complexidade operacional extra (monitoramento, backups separados, infraestrutura adicional).

## Decisão
Usaremos o **PostgreSQL** como fila de mensagens.

## Consequências
### Prós
1. **Transacionalidade (ACID):** O job é inserido na mesma transação que os dados de negócio. Se um erro ocorrer, o job nunca é criado.
2. **Menos Infra:** Não precisamos subir e manter um Redis.
3. **Persistência: Além de fila, o banco guarda o histórico de jobs e payloads.**
4. **Tooling:** Podemos usar SQL puro para depurar, migrar e gerenciar os jobs.

### Contras
1. **Performance de Escrita:** PostgreSQL tem mais overhead que Redis para inserções massivas (milhares por segundo).
2. **Polling/Triggers:** Requer LISTEN/NOTIFY ou polling para despertar workers, o que consome conexões.
