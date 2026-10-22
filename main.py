import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import settings
from queue_manager import process_queue_worker, redis_client

# Импорт роутеров
from routers import generation, models, system

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# 🔥 Ключ из .env или запасной
EXPECTED_API_KEY = os.getenv("API_KEY", "meow_super_secret_key_3060")


# 🔥 УМНЫЙ СТРАЖ (Middleware)
class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Проверяем, пришел ли запрос через прокси (Cloudflare Tunnel всегда добавляет эти заголовки)
        is_from_proxy = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for")

        # 2. Если запрос НАСТОЯЩИЙ локальный (без прокси и с localhost), пропускаем без ключа
        if not is_from_proxy and request.client.host in ["127.0.0.1", "::1"]:
            return await call_next(request)

        # 3. Для ВСЕХ остальных (включая /docs извне и запросы через туннель) требуем ключ
        api_key = request.headers.get("x-api-key")
        if api_key != EXPECTED_API_KEY:
            logger.warning(f"🚫 Отказано в доступе к {request.url.path} с IP: {request.client.host}")
            return JSONResponse(status_code=401, content={"detail": "Неверный API ключ. Доступ закрыт."})

        return await call_next(request)


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
    docs_url="/docs",  # Можно поставить None, чтобы вообще скрыть извне
    redoc_url="/redoc"
)

# 🔥 Подключаем стража ко ВСЕМ запросам приложения
app.add_middleware(SecurityMiddleware)

# Подключаем роутеры
app.include_router(generation.router)
app.include_router(models.router)
app.include_router(system.router)