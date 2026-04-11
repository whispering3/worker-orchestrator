import asyncpg

FETCH_SQL = """
  UPDATE jobs
  SET status = 'running',
      started_at = now(),
      lease_expires_at = now() + interval '5 minutes', -- Lease de 5 minutos
      attempts = attempts + 1
  WHERE id = (
    SELECT id FROM jobs
    WHERE queue = $1
      AND (
        status = 'pending' 
        OR (status = 'running' AND lease_expires_at < now()) -- Pega jobs zumbis
      )
      AND run_at <= now()
    ORDER BY priority DESC, run_at ASC
    FOR UPDATE SKIP LOCKED
    LIMIT 1
  )
  RETURNING *
"""

async def fetch_next(conn, queue: str):
    """
    Busca o próximo job disponível atomicamente usando SKIP LOCKED.
    Também recupera jobs que expiraram o lease (zumbis).
    """
    return await conn.fetchrow(FETCH_SQL, queue)
