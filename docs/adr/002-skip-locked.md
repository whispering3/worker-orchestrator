# ADR 002: SELECT FOR UPDATE SKIP LOCKED

## Status
Proposto

## Contexto
Em uma fila baseada em banco de dados com múltiplos workers, o maior desafio é garantir que dois workers não processem o mesmo job simultaneamente (race condition).

## Decisão
Usaremos a cláusula `FOR UPDATE SKIP LOCKED`.

## Detalhes Técnicos
Ao buscar um job, o PostgreSQL tenta travar a linha (`FOR UPDATE`). Se a linha já estiver travada por outra transação, em vez de esperar (que causaria gargalo de concorrência), ele simplesmente pula (`SKIP LOCKED`) e vai para a próxima linha disponível.

## Consequências
### Prós
1. **Concorrência Perfeita:** Workers não bloqueiam uns aos outros.
2. **Escalabilidade:** Permite escalar horizontalmente o número de workers sem colisão.
3. **Simplicidade:** Implementado nativamente no motor do banco (PG 9.5+).

### Contras
1. **Transações Longas:** Se o worker demorar a processar, ele mantém o lock e a transação aberta. Resolvemos isso usando um `lease` (expiração) e transações curtas para o fetch.
