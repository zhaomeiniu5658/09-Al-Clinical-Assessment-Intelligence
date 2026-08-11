import hashlib
import hmac
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.v1.knowledge import _response
from app.db.session import get_db
from app.models.knowledge import KnowledgeCategory, KnowledgeEntry, KnowledgeExternalApiSettings
from app.schemas.knowledge import KnowledgeCategoryResponse, KnowledgeEntryResponse, KnowledgeListResponse

router = APIRouter(prefix="/external/knowledge", tags=["external knowledge"])
api_key_header = APIKeyHeader(name="X-Knowledge-API-Key", auto_error=False)


def _verify_api_key(api_key: str | None, db: Session) -> None:
    config = db.get(KnowledgeExternalApiSettings, 1)
    if not config or not config.is_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="知识库对外 API 未开通")
    if not api_key or not config.api_key_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少 API Key")
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(digest, config.api_key_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key 无效")


def _entry_or_404(db: Session, entry_id: int) -> KnowledgeEntry:
    entry = db.scalar(
        select(KnowledgeEntry)
        .options(joinedload(KnowledgeEntry.created_by))
        .where(KnowledgeEntry.id == entry_id)
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库条目不存在")
    return entry


@router.get("/categories", response_model=list[KnowledgeCategoryResponse])
def list_external_categories(
    api_key: Annotated[str | None, Security(api_key_header)],
    db: Annotated[Session, Depends(get_db)],
) -> list[KnowledgeCategory]:
    _verify_api_key(api_key, db)
    return db.scalars(select(KnowledgeCategory).order_by(KnowledgeCategory.name)).all()


@router.get("/{entry_id}/attachment")
def get_external_attachment(
    entry_id: int,
    api_key: Annotated[str | None, Security(api_key_header)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    _verify_api_key(api_key, db)
    entry = _entry_or_404(db, entry_id)
    if not entry.attachment_path or not Path(entry.attachment_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件不存在")
    return FileResponse(entry.attachment_path, media_type=entry.attachment_mime_type, filename=entry.attachment_name)


@router.get("", response_model=KnowledgeListResponse)
def list_external_entries(
    api_key: Annotated[str | None, Security(api_key_header)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    page_size: int = 10,
    keyword: str = "",
    category: str = "",
) -> KnowledgeListResponse:
    _verify_api_key(api_key, db)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    statement = select(KnowledgeEntry).options(joinedload(KnowledgeEntry.created_by))
    if keyword.strip():
        like = f"%{keyword.strip()}%"
        statement = statement.where(KnowledgeEntry.title.ilike(like) | KnowledgeEntry.content.ilike(like))
    if category.strip():
        statement = statement.where(KnowledgeEntry.category == category.strip())
    total = db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
    entries = db.scalars(
        statement.order_by(KnowledgeEntry.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return KnowledgeListResponse(items=[_response(entry) for entry in entries], total=total, page=page, page_size=page_size)


@router.get("/{entry_id}", response_model=KnowledgeEntryResponse)
def get_external_entry(
    entry_id: int,
    api_key: Annotated[str | None, Security(api_key_header)],
    db: Annotated[Session, Depends(get_db)],
) -> KnowledgeEntryResponse:
    _verify_api_key(api_key, db)
    return _response(_entry_or_404(db, entry_id))
