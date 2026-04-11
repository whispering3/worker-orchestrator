import asyncio
import pytest
import asyncpg
from orchestrator.pool import WorkerPool

DATABASE_URL = "postgresql://user:password@localhost:5432/orchestrator"

@pytest.mark.asyncio
async def test_worker_pool_processing():
    """
    Testa o fluxo completo do WorkerPool: submissão -> processamento -> status done.
    """
    pool = await asyncpg.create_pool(DATABASE_URL)
    
    # 1. Limpa jobs
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM jobs")

    # 2. Define um handler que apenas marca como processado
    processed_jobs = []
    async def sample_handler(job_payload):
        processed_jobs.append(job_payload)
        await asyncio.sleep(0.1)

    # 3. Inicia o WorkerPool
    worker = WorkerPool(queue='test_pool', concurrency=2, handler=sample_handler, pool=pool)
    worker_task = asyncio.create_task(worker.run())

    # 4. Insere alguns jobs via banco (como se fosse a API)
    async with pool.acquire() as conn:
        for i in range(5):
            await conn.execute("""
                INSERT INTO jobs (queue, payload) VALUES ('test_pool', $1)
            """, f'{{"id": {i}}}')

    # 5. Espera um pouco para o processamento ocorrer
    # O LISTEN/NOTIFY deve disparar o processamento
    await asyncio.sleep(1.0)

    # 6. Verifica resultados
    assert len(processed_jobs) == 5
    
    async with pool.acquire() as conn:
        done_count = await conn.fetchval("SELECT count(*) FROM jobs WHERE status = 'done'")
        assert done_count == 5

    # 7. Finaliza
    worker.stop()
    worker_task.cancel()
    await pool.close()
