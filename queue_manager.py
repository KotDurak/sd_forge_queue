import json
import logging
import redis.asyncio as redis
from config import settings
from forge_client import call_forge_api

logger = logging.getLogger(__name__)

# Глобальный клиент Redis
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def add_task_to_queue(task_id: str, payload: dict):
    """Создает задачу и добавляет в очередь"""
    task_data = {
        "task_id": task_id,
        "status": "queued",
        "payload": payload,
        "result_b64": None,
        "error": None
    }
    await redis_client.setex(f"task:{task_id}", settings.TASK_TTL_SECONDS, json.dumps(task_data))
    await redis_client.lpush("generation_queue", task_id)


async def get_task_status(task_id: str) -> dict:
    """Получает статус. Если completed, возвращает структуру как у Forge."""
    task_json = await redis_client.get(f"task:{task_id}")
    if not task_json:
        return {"status": "not_found"}

    task = json.loads(task_json)

    if task["status"] == "completed":
        # Возвращаем формат, совместимый с ботом
        return {
            "status": "completed",
            "images": [task["result_b64"]],
            "parameters": task["payload"]
        }

    return {"status": task["status"], "error": task.get("error")}


async def process_queue_worker():
    """Бесконечный воркер, обрабатывающий очередь"""
    logger.info("🚀 Воркер очереди запущен")

    while True:
        # Ждем задачу из очереди
        result = await redis_client.brpop("generation_queue", timeout=1)
        if not result:
            continue

        _, task_id = result

        # 🔥 ПРОВЕРКА: не умерла ли задача в очереди из-за TTL?
        task_json = await redis_client.get(f"task:{task_id}")
        if not task_json:
            logger.warning(f"⚠️ Задача {task_id} умерла в очереди (TTL истек). Пропускаем.")
            continue

        task = json.loads(task_json)
        task["status"] = "processing"

        # 🔥 ПРОДЛЕВАЕМ TTL при начале обработки
        await redis_client.setex(f"task:{task_id}", settings.TASK_TTL_SECONDS, json.dumps(task))

        try:
            # Вызываем наш асинхронный клиент Forge
            image_bytes = await call_forge_api(task["payload"])

            if image_bytes:
                import base64
                task["status"] = "completed"
                task["result_b64"] = base64.b64encode(image_bytes).decode('utf-8')
                logger.info(f"✅ Задача {task_id} успешно завершена")
            else:
                raise Exception("Forge вернул пустой результат или ошибку")

        except Exception as e:
            logger.error(f"❌ Ошибка для задачи {task_id}: {e}")
            task["status"] = "failed"
            task["error"] = str(e)

        # 🔥 ПРОДЛЕВАЕМ TTL после завершения (успешного или нет)
        await redis_client.setex(f"task:{task_id}", settings.TASK_TTL_SECONDS, json.dumps(task))