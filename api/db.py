import os
import json
import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5433/orchestrator")

async def init_connection(conn):
    await conn.set_type_codec(
        'jsonb',
        encoder=json.dumps,
        decoder=json.loads,
        schema='pg_catalog'
    )
    await conn.set_type_codec(
        'json',
        encoder=json.dumps,
        decoder=json.loads,
        schema='pg_catalog'
    )

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            DATABASE_URL,
            init=init_connection
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

db = Database()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()
