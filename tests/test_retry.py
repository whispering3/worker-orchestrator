import pytest
import asyncpg
from datetime import datetime, timezone
from orchestrator.retry import handle_failure

DATABASE_URL = "postgresql://user:password@localhost:5432/orchestrator"

@pytest.mark.asyncio
async def test_retry_backoff_and_dlq():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("DELETE FROM jobs")
    
    # 1. Insere um job com max_attempts=2
    job_id = await conn.fetchval("""
        INSERT INTO jobs (queue, payload, max_attempts, attempts) 
        VALUES ('retry_test', '{}', 2, 1)
        RETURNING id
    """)
    
    job = await conn.fetchrow("SELECT * FROM jobs WHERE id = $1", job_id)
    
    # 2. Simula primeira falha (deve ir para pending com delay)
    await handle_failure(conn, job, "Erro de teste 1")
    
    updated_job = await conn.fetchrow("SELECT * FROM jobs WHERE id = $1", job_id)
    assert updated_job['status'] == 'pending'
    assert updated_job['last_error'] == "Erro de teste 1"
    assert updated_job['run_at'] > datetime.now(timezone.utc)
    
    # 3. Simula segunda tentativa e falha final (deve ir para dead)
    # Incrementamos attempts como o fetch real faria
    await conn.execute("UPDATE jobs SET attempts = 2 WHERE id = $1", job_id)
    job = await conn.fetchrow("SELECT * FROM jobs WHERE id = $1", job_id)
    
    await handle_failure(conn, job, "Erro fatal")
    
    final_job = await conn.fetchrow("SELECT * FROM jobs WHERE id = $1", job_id)
    assert final_job['status'] == 'dead'
    assert final_job['last_error'] == "Erro fatal"
    
    await conn.close()
