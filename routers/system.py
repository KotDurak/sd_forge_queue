import logging
from fastapi import APIRouter
from schemas.task import QueueStatsResponse
from queue_manager import redis_client
from forge_client import get_forge_progress

logger = logging.getLogger(__name__)
router = APIRouter(tags=["System"])

@router.get("/sdapi/v1/progress", summary="Глобальный прогресс Forge")
async def get_global_progress():
    return await get_forge_progress()

@router.get("/sdapi/v1/queue/stats", response_model=QueueStatsResponse, summary="Статистика очереди")
async def get_queue_stats():
    length = await redis_client.llen("generation_queue")
    return {"queue_length": length, "estimated_wait_seconds": length * 15}