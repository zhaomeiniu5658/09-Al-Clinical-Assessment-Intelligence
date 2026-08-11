from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class KnowledgeEntryResponse(BaseModel):
    id: int
    title: str
    category: str
    summary: str | None
    content: str
    attachment_name: str | None
    attachment_mime_type: str | None
    attachment_size: int | None
    created_by_id: int
    created_by_username: str
    created_at: datetime
    updated_at: datetime


class KnowledgeListResponse(BaseModel):
    items: list[KnowledgeEntryResponse]
    total: int
    page: int
    page_size: int


class KnowledgeCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("分类名称不能为空")
        return normalized


class KnowledgeCategoryResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeExternalApiSettingsUpdate(BaseModel):
    is_enabled: bool
    regenerate_key: bool = False


class KnowledgeExternalApiSettingsResponse(BaseModel):
    is_enabled: bool
    key_configured: bool
    api_key_prefix: str | None
    api_key: str | None = None
    updated_at: datetime | None
