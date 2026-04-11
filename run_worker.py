import json
import asyncio
import asyncpg
import logging
from orchestrator.pool import WorkerPool

logging.basicConfig(level=logging.INFO)

async def init_connection(conn):
    await conn.set_type_codec(
        'jsonb',
        encoder=json.dumps,
        decoder=json.loads,
        schema='pg_catalog'
    )

async def my_handler(job):
    print(f"Processando Job {job['id']} | Payload: {job['payload']}")
    await asyncio.sleep(2) # Simula trabalho pesado
    if job['payload'].get('fail'):
        raise Exception("Falha simulada!")

async def main():
    # URL do banco definida no docker-compose
    DATABASE_URL = "postgresql://user:password@localhost:5433/orchestrator"
    
    # Aguarda o banco ficar pronto se necessário
    pool = None
    for i in range(10):
        try:
            pool = await asyncpg.create_pool(DATABASE_URL, init=init_connection)
            break
        except Exception:
            await asyncio.sleep(2)
            
    if not pool:
        print("Não foi possível conectar ao banco.")
        return

    worker = WorkerPool(queue='default', concurrency=3, handler=my_handler, pool=pool)
    print("Worker aguardando jobs...")
    try:
        await worker.run()
    except asyncio.CancelledError:
        await pool.close()

if __name__ == "__main__":
    asyncio.run(main())
