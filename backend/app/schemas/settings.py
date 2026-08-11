from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, Field


class XfyunAsrSettingsResponse(BaseModel):
    model_name: str
    app_id: str
    web_api: str
    hotwords: str | None
    api_secret_configured: bool
    api_key_configured: bool
    updated_at: datetime | None


class XfyunAsrSettingsUpdate(BaseModel):
    model_name: str = Field(..., min_length=1, max_length=128)
    app_id: str = Field(..., min_length=1, max_length=255)
    api_secret: str | None = Field(default=None, max_length=512)
    api_key: str | None = Field(default=None, max_length=512)
    web_api: AnyHttpUrl
    hotwords: str | None = Field(default=None, max_length=10000)
