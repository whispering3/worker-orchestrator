import asyncio
import pytest
import asyncpg
from orchestrator.fetch import fetch_next

DATABASE_URL = "postgresql://user:password@localhost:5432/orchestrator"

@pytest.mark.asyncio
async def test_atomic_fetch_skip_locked():
    """
    Testa se o SKIP LOCKED realmente evita que dois workers peguem o mesmo job.
    """
    pool = await asyncpg.create_pool(DATABASE_URL)
    
    # 1. Limpa jobs e insere um único job
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM jobs")
        await conn.execute("""
            INSERT INTO jobs (queue, payload) VALUES ('test_queue', '{"data": 123}')
        """)

    # 2. Tenta buscar simultaneamente com dois "workers"
    async def try_fetch():
        async with pool.acquire() as conn:
            # Iniciamos uma transação explicitamente para segurar o lock
            async with conn.transaction():
                job = await fetch_next(conn, 'test_queue')
                if job:
                    await asyncio.sleep(0.5) # Simula processamento curto segurando o lock
                return job

    # Executamos em paralelo
    results = await asyncio.gather(try_fetch(), try_fetch())

    # 3. Verifica que apenas UM worker conseguiu o job
    jobs_fetched = [r for r in results if r is not None]
    assert len(jobs_fetched) == 1
    
    await pool.close()
