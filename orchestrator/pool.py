import asyncio
import logging
import asyncpg
from typing import Callable, Awaitable, Dict, Any
from .fetch import fetch_next
from .retry import handle_failure

logger = logging.getLogger(__name__)

async def mark_done(conn, job_id):
    await conn.execute("""
        UPDATE jobs 
        SET status = 'done', finished_at = now(), lease_expires_at = NULL
        WHERE id = $1
    """, job_id)

class WorkerPool:
    def __init__(
        self, 
        queue: str, 
        concurrency: int, 
        handler: Callable[[Dict[str, Any]], Awaitable[None]],
        pool: asyncpg.Pool
    ):
        self.queue = queue
        self.concurrency = concurrency
        self.handler = handler
        self.pool = pool
        self.semaphore = asyncio.Semaphore(concurrency)
        self._listener_conn = None
        self._running = False

    async def run(self):
        self._running = True
        # Usamos uma conexão dedicada do pool para o LISTEN
        self._listener_conn = await self.pool.acquire()
        try:
            await self._listener_conn.add_listener('job_available', self._on_notify)
            logger.info(f"WorkerPool iniciado para a fila '{self.queue}' (concurrency={self.concurrency})")
            
            # Iniciamos um loop de poll periódico para jobs agendados que perderam o NOTIFY
            asyncio.create_task(self._periodic_drain())
            
            # Loop infinito para manter o worker vivo
            while self._running:
                await asyncio.sleep(1)
        finally:
            await self._listener_conn.remove_listener('job_available', self._on_notify)
            await self.pool.release(self._listener_conn)

    async def _periodic_drain(self):
        """Drena periodicamente para garantir que não perdemos jobs agendados"""
        while self._running:
            await self._drain()
            await asyncio.sleep(30) # Poll a cada 30 segundos

    async def _on_notify(self, conn, pid, channel, payload):
        """Callback acionado pelo PostgreSQL LISTEN/NOTIFY"""
        if payload == self.queue:
            # Acionamos o processamento em background
            asyncio.create_task(self._process_one())

    async def _drain(self):
        """Processa jobs pendentes até que não sobre nenhum"""
        while True:
            # Pegamos uma conexão do pool para checar
            async with self.pool.acquire() as conn:
                job = await fetch_next(conn, self.queue)
                if not job:
                    break
                asyncio.create_task(self._process_one(job))

    async def _process_one(self, job=None):
        """Tenta processar um job, respeitando a concorrência"""
        async with self.semaphore:
            async with self.pool.acquire() as conn:
                # Se não recebemos um job pronto, buscamos o próximo
                if not job:
                    job = await fetch_next(conn, self.queue)
                
                if not job:
                    return

                job_id = job['id']
                try:
                    logger.info(f"Processando job {job_id} na fila {self.queue}")
                    await self.handler(dict(job))
                    await mark_done(conn, job_id)
                    logger.info(f"Job {job_id} concluído com sucesso")
                except Exception as e:
                    logger.error(f"Erro ao processar job {job_id}: {e}")
                    # Passamos para o handler de falha (retry/DLQ)
                    await handle_failure(conn, job, e)

    def stop(self):
        self._running = False
