from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
from .db import db

router = APIRouter(prefix="/jobs", tags=["Jobs"])

class JobCreate(BaseModel):
    queue: str = "default"
    payload: Dict[str, Any]
    priority: int = 0
    max_attempts: int = 3

@router.post("")
async def create_job(job: JobCreate):
    """Submete um novo job para a fila."""
    job_id = await db.pool.fetchval("""
        INSERT INTO jobs (queue, payload, priority, max_attempts)
        VALUES ($1, $2, $3, $4)
        RETURNING id
    """, job.queue, job.payload, job.priority, job.max_attempts)
    
    return {"id": job_id, "status": "pending"}

@router.get("/{job_id}")
async def get_job(job_id: str):
    """Busca o status de um job pelo ID."""
    job = await db.pool.fetchrow("SELECT * FROM jobs WHERE id = $1", job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return dict(job)
