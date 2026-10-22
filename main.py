import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException  # 🔥 Добавили Request, Depends, HTTPException

from config import settings
from queue_manager import process_queue_worker, redis_client

# Импорт роутеров
from routers import generation, models, system

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# 🔥 ГЛОБАЛЬНАЯ ЗАЩИТА: Ключ берем из .env, или используем запасной
EXPECTED_API_KEY = os.getenv("API_KEY", "meow_super_secret_key_3060")


# 🔥 Функция-страж (Dependency)
async def verify_access(request: Request):
    # 1. Если запрос локальный (с этого же ПК) — пропускаем без вопросов
    if request.client.host in ["127.0.0.1", "::1"]:
        return

    # 2. Если запрос извне — требуем правильный ключ в заголовке
    api_key = request.headers.get("x-api-key")
    if api_key != EXPECTED_API_KEY:
        logger.warning(f"🚫 Попытка доступа с чужим ключом с IP: {request.client.host}")
        raise HTTPException(status_code=401, detail="Неверный API ключ. Доступ закрыт.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await redis_client.ping()
        logger.info("✅ Связь с Redis (Memurai) установлена")
        asyncio.create_task(process_queue_worker())
        logger.info("🐈‍⬛ API Gateway запущен. Барсик одобряет. Ветчина в безопасности.")
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА при запуске: {e}")
    yield
    # Shutdown
    logger.info("🛑 API Gateway останавливается...")


app = FastAPI(
    title="SD Forge Gateway API",
    description="Умная прослойка с очередью Redis для Stable Diffusion Forge.",
    version="1.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    dependencies=[Depends(verify_access)]  # 🔥 ГЛОБАЛЬНОЕ ПРИМЕНЕНИЕ СТРАЖА КО ВСЕМ МАРШРУТАМ
)

# Подключаем роутеры (теперь они автоматически защищены для внешних запросов)
app.include_router(generation.router)
app.include_router(models.router)
app.include_router(system.router)