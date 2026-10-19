import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Настройки шлюза
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    API_PORT = int(os.getenv("API_PORT", 8000))
    TASK_TTL_SECONDS = int(os.getenv("TASK_TTL_SECONDS", 600))

    # Настройки SD Forge
    FORGE_URL = os.getenv("SD_FORGE_URL", "http://127.0.0.1:7860")

    # Аутентификация Forge (если есть, формат: "user:pass" или None)
    AUTH_STR = os.getenv("FORGE_AUTH")
    FORGE_AUTH = tuple(AUTH_STR.split(":")) if AUTH_STR else None


settings = Settings()