import logging
import uuid
import asyncio
from fastapi import FastAPI, HTTPException
from config import settings
from queue_manager import add_task_to_queue, get_task_status, process_queue_worker, redis_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="SD Gateway API")


@app.on_event("startup")
async def startup_event():
    # Проверяем связь с Redis
    await redis_client.ping()
    logger.info("✅ Связь с Redis установлена")
    # Запускаем воркер в фоне
    asyncio.create_task(process_queue_worker())
    logger.info("🐈‍⬛ API Gateway запущен. Барсик одобряет.")


@app.post("/sdapi/v1/txt2img")
async def create_generation_task(payload: dict):
    task_id = str(uuid.uuid4())
    await add_task_to_queue(task_id, payload)
    logger.info(f"📥 Задача {task_id} добавлена в очередь")
    return {"task_id": task_id, "status": "queued"}


@app.get("/sdapi/v1/task/{task_id}")
async def get_task_status_route(task_id: str):
    result = await get_task_status(task_id)
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Задача не найдена или срок её жизни истек")

    # Если задача завершена, логируем это красиво
    if result.get("status") == "completed":
        logger.info(f"🎨 Задача {task_id} отдает результат: status=completed")

    return result


@app.get("/sdapi/v1/queue/stats")
async def get_queue_stats():
    length = await redis_client.llen("generation_queue")
    return {"queue_length": length, "estimated_wait_seconds": length * 15}