import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from config import settings
from queue_manager import process_queue_worker, redis_client

# Импорт роутеров
from routers import generation, models, system

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

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
    redoc_url="/redoc"
)

# Подключаем роутеры
app.include_router(generation.router)
app.include_router(models.router)
app.include_router(system.router)