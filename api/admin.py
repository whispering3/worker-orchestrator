from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from .db import db

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/dlq")
async def get_dlq_jobs(queue: str = "default"):
    """Lista jobs na Dead Letter Queue."""
    jobs = await db.pool.fetch("""
        SELECT * FROM jobs 
        WHERE status = 'dead' AND queue = $1
        ORDER BY created_at DESC
    """, queue)
    return [dict(j) for j in jobs]

@router.post("/dlq/{job_id}/reprocess")
async def reprocess_job(job_id: str):
    """Reinjeta um job falho na fila, resetando tentativas."""
    result = await db.pool.execute("""
        UPDATE jobs 
        SET status = 'pending', 
            attempts = 0, 
            run_at = now(),
            last_error = NULL,
            finished_at = NULL,
            lease_expires_at = NULL
        WHERE id = $1 AND status = 'dead'
    """, job_id)
    
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Job not found or not in DLQ")
    
    return {"message": f"Job {job_id} reinjected into queue"}

@router.delete("/dlq/{job_id}")
async def delete_job(job_id: str):
    """Remove um job da DLQ."""
    result = await db.pool.execute("DELETE FROM jobs WHERE id = $1 AND status = 'dead'", job_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Job not found in DLQ")
    return {"message": "Job deleted"}
