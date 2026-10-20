import uuid
import logging
from fastapi import APIRouter, HTTPException
from schemas.task import Txt2ImgRequest, TaskStatusResponse
from queue_manager import add_task_to_queue, get_task_status

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Generation"])


@router.post("/sdapi/v1/txt2img", response_model=dict, summary="Поставить задачу в очередь")
async def create_generation_task(payload: Txt2ImgRequest):
    task_id = str(uuid.uuid4())
    await add_task_to_queue(task_id, payload.model_dump())
    logger.info(f"📥 Задача {task_id} добавлена в очередь")
    return {"task_id": task_id, "status": "queued"}


@router.get("/sdapi/v1/task/{task_id}", response_model=TaskStatusResponse, summary="Получить статус задачи")
async def get_task_status_route(task_id: str):
    result = await get_task_status(task_id)

    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Задача не найдена или срок её жизни истек")

    # 🔥 Умный патч: гарантируем, что response_model будет удовлетворен
    if "task_id" not in result:
        result["task_id"] = task_id

    if "images" in result and isinstance(result["images"], list) and len(result["images"]) > 0:
        result["image"] = result["images"][0]

    if result.get("status") in ["complete", "success"]:
        result["status"] = "completed"

    if result.get("status") == "completed":
        logger.info(f"🎨 Задача {task_id} отдает результат: status=completed")

    return result