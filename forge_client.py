import logging
import time
import base64
import httpx
from config import settings

logger = logging.getLogger(__name__)

# 🔥 ИСПРАВЛЕНИЕ: Создаем клиент БЕЗ base_url, добавляем расширенный таймаут
forge_client = httpx.AsyncClient(
    timeout=httpx.Timeout(300.0, connect=30.0),  # 30 сек на подключение, 300 сек на чтение
    trust_env=False,
    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
)


async def call_forge_api(payload: dict) -> bytes | None:
    """🔥 Принимает готовый payload. Отправляет асинхронно."""
    # Формируем ПОЛНЫЙ URL вручную
    url = f"{settings.FORGE_URL}/sdapi/v1/txt2img"
    start = time.time()

    try:
        logger.info(f"🔗 Отправка запроса на {url}")

        response = await forge_client.post(
            url,
            json=payload,
            auth=settings.FORGE_AUTH,
        )
        response.raise_for_status()
        res = response.json()

        logger.info(f"⏱ Ответ Forge за {time.time() - start:.2f}с | Статус: {response.status_code}")

        if res.get("images"):
            return base64.b64decode(res["images"][0])
        logger.error("❌ В ответе Forge нет изображений")
        return None

    except httpx.ConnectError as e:
        logger.error(f"🔌 ConnectError: Не удалось подключиться к {url}. Ошибка: {e}")
        return None
    except httpx.TimeoutException as e:
        logger.error(f"⏰ TimeoutException: Forge не ответил за 300 сек. Ошибка: {e}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ HTTP {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        logger.error(f"❌ API error ({type(e).__name__}): {e}")
        return None


# Остальные функции тоже нужно обновить, используя полный URL:
async def fetch_available_models() -> list[tuple[str, str]]:
    try:
        url = f"{settings.FORGE_URL}/sdapi/v1/sd-models"
        resp = await forge_client.get(url, auth=settings.FORGE_AUTH)
        resp.raise_for_status()
        return [(m.get('model_name', m['title']), m['title']) for m in resp.json()]
    except Exception as e:
        logger.error(f"❌ Не удалось получить модели: {e}")
        return []


async def fetch_available_vae() -> list[tuple[str, str]]:
    try:
        url = f"{settings.FORGE_URL}/sdapi/v1/sd-modules"
        resp = await forge_client.get(url, auth=settings.FORGE_AUTH)
        resp.raise_for_status()
        result = [("🤖 Automatic (встроенный)", "Automatic")]
        for v in resp.json():
            name = v.get('model_name', v.get('filename', ''))
            label = name.replace('.safetensors', '')
            result.append((label, name))
        return result
    except Exception as e:
        logger.error(f"❌ Не удалось получить VAE: {e}")
        return [("🤖 Automatic", "Automatic")]


async def switch_forge_model(model_checkpoint: str) -> bool:
    try:
        url = f"{settings.FORGE_URL}/sdapi/v1/options"
        resp = await forge_client.post(
            url,
            json={"sd_model_checkpoint": model_checkpoint},
            auth=settings.FORGE_AUTH,
            timeout=45.0
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка смены модели: {e}")
        return False


async def fetch_available_loras() -> list[dict]:
    try:
        url = f"{settings.FORGE_URL}/sdapi/v1/loras"
        resp = await forge_client.get(url, auth=settings.FORGE_AUTH, timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"❌ Ошибка получения LoRA: {e}")
        return []


async def get_forge_progress() -> dict:
    try:
        url = f"{settings.FORGE_URL}/sdapi/v1/progress"
        resp = await forge_client.get(url, auth=settings.FORGE_AUTH, timeout=5.0)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {'progress': 0.0, 'eta_relative': 0}