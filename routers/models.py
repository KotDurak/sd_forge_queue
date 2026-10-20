import logging
from fastapi import APIRouter, HTTPException
from forge_client import fetch_available_models, fetch_available_vae, fetch_available_loras, switch_forge_model

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Models & Config"])

@router.get("/sdapi/v1/sd-models", summary="Список чекпоинтов")
async def get_models():
    return {"models": await fetch_available_models()}

@router.get("/sdapi/v1/sd-vae", summary="Список VAE")
async def get_vae():
    return {"vaes": await fetch_available_vae()}

@router.get("/sdapi/v1/loras", summary="Список LoRA")
async def get_loras():
    return {"loras": await fetch_available_loras()}

@router.post("/sdapi/v1/options", summary="Смена настроек Forge")
async def update_options(options: dict):
    success = await switch_forge_model(options.get("sd_model_checkpoint", ""))
    if not success:
        raise HTTPException(status_code=500, detail="Не удалось сменить настройки")
    return {"message": "Настройки успешно обновлены"}