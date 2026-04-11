import random
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

async def handle_failure(conn, job, error):
    """
    Trata falhas de execução com backoff exponencial e promoção para DLQ (Dead Letter Queue).
    """
    job_id = job['id']
    attempts = job['attempts']
    max_attempts = job['max_attempts']

    if attempts >= max_attempts:
        # Manda para a dead-letter queue (status 'dead')
        logger.warning(f"Job {job_id} atingiu o limite de tentativas ({max_attempts}). Movendo para DLQ.")
        await conn.execute("""
            UPDATE jobs SET 
                status = 'dead',
                last_error = $2, 
                finished_at = now(),
                lease_expires_at = NULL
            WHERE id = $1
        """, job_id, str(error))
        return

    # Backoff exponencial: 2^attempt * 30s
    # Adicionamos Jitter para evitar "retry storms"
    base_delay = (2 ** (attempts - 1)) * 30  # Usamos attempts-1 pois já incrementamos no fetch
    jitter = random.uniform(0.8, 1.2)        # ±20% de variação
    delay_seconds = base_delay * jitter
    
    run_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

    logger.info(f"Job {job_id} falhou. Agendando retry em {delay_seconds:.1f}s (run_at={run_at})")

    await conn.execute("""
        UPDATE jobs SET 
            status = 'pending',
            last_error = $2, 
            run_at = $3,
            lease_expires_at = NULL
        WHERE id = $1
    """, job_id, str(error), run_at)
