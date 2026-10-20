from pydantic import BaseModel, Field
from typing import Optional, Any
# ==========================================
# 📦 Pydantic-модели для Swagger
# ==========================================

class Txt2ImgRequest(BaseModel):
    """Параметры для генерации (совместимы с SD Forge API)"""
    prompt: str = Field(..., description="Основной промпт", example="1girl, masterpiece, best quality, purple hair")
    negative_prompt: str = Field("", description="Негативный промпт", example="lowres, bad anatomy")
    steps: int = Field(20, description="Количество шагов", ge=1, le=150)
    width: int = Field(512, description="Ширина", ge=64, le=2048)
    height: int = Field(512, description="Высота", ge=64, le=2048)

    # Разрешаем любые дополнительные параметры Forge (cfg_scale, sampler_name и т.д.)
    class Config:
        extra = "allow"


class TaskStatusResponse(BaseModel):
    """Ответ со статусом задачи. Максимально гибкий."""
    task_id: str = Field(..., description="ID задачи")
    status: str = Field(..., description="queued, processing, completed, failed, not_found")
    progress: Optional[Any] = Field(None, description="Прогресс (float или str)")
    image: Optional[str] = Field(None, description="Base64 строка первого изображения")
    images: Optional[list[str]] = Field(None, description="Список всех изображений (если их несколько)")
    error: Optional[str] = Field(None, description="Текст ошибки")

    class Config:
        extra = "allow"  # Позволяет игнорировать любые другие неожиданные поля из Redis


class QueueStatsResponse(BaseModel):
    queue_length: int
    estimated_wait_seconds: int