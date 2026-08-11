from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings as app_settings
from app.db.session import get_db
from app.models.system import XfyunAsrSettings
from app.models.user import User
from app.schemas.settings import XfyunAsrSettingsResponse, XfyunAsrSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


def _get_or_create(db: Session) -> XfyunAsrSettings:
    config = db.get(XfyunAsrSettings, 1)
    if config:
        return config
    config = XfyunAsrSettings(
        id=1,
        model_name="非实时语音转写大模型",
        app_id=app_settings.xfyun_app_id,
        api_secret=app_settings.xfyun_api_secret,
        api_key=app_settings.xfyun_api_key,
        web_api="https://office-api-ist-dx.iflyaisol.com",
        hotwords=None,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def _response(config: XfyunAsrSettings) -> XfyunAsrSettingsResponse:
    return XfyunAsrSettingsResponse(
        model_name=config.model_name,
        app_id=config.app_id,
        web_api=config.web_api,
        hotwords=config.hotwords,
        api_secret_configured=bool(config.api_secret),
        api_key_configured=bool(config.api_key),
        updated_at=config.updated_at,
    )


@router.get("/xfyun-asr", response_model=XfyunAsrSettingsResponse)
def get_xfyun_asr_settings(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> XfyunAsrSettingsResponse:
    return _response(_get_or_create(db))


@router.put("/xfyun-asr", response_model=XfyunAsrSettingsResponse)
def update_xfyun_asr_settings(
    payload: XfyunAsrSettingsUpdate,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> XfyunAsrSettingsResponse:
    config = _get_or_create(db)
    config.model_name = payload.model_name.strip()
    config.app_id = payload.app_id.strip()
    config.web_api = str(payload.web_api).rstrip("/")
    config.hotwords = payload.hotwords.strip() if payload.hotwords else None
    if payload.api_secret and payload.api_secret.strip():
        config.api_secret = payload.api_secret.strip()
    if payload.api_key and payload.api_key.strip():
        config.api_key = payload.api_key.strip()
    db.commit()
    db.refresh(config)
    return _response(config)
