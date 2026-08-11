import hashlib
import secrets
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.knowledge import KnowledgeCategory, KnowledgeEntry, KnowledgeExternalApiSettings
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeCategoryCreate,
    KnowledgeCategoryResponse,
    KnowledgeEntryResponse,
    KnowledgeExternalApiSettingsResponse,
    KnowledgeExternalApiSettingsUpdate,
    KnowledgeListResponse,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

ALLOWED_ATTACHMENT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".txt",
    ".md",
    ".csv",
    ".xls",
    ".xlsx",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".svg",
    ".tif",
    ".tiff",
    ".heic",
}


def _require_admin(current_user: User) -> None:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可以维护知识库")


def _entry_or_404(db: Session, entry_id: int) -> KnowledgeEntry:
    entry = db.scalar(
        select(KnowledgeEntry)
        .options(joinedload(KnowledgeEntry.created_by))
        .where(KnowledgeEntry.id == entry_id)
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识库条目不存在")
    return entry


def _response(entry: KnowledgeEntry) -> KnowledgeEntryResponse:
    return KnowledgeEntryResponse(
        id=entry.id,
        title=entry.title,
        category=entry.category,
        summary=entry.summary,
        content=entry.content,
        attachment_name=entry.attachment_name,
        attachment_mime_type=entry.attachment_mime_type,
        attachment_size=entry.attachment_size,
        created_by_id=entry.created_by_id,
        created_by_username=entry.created_by.username,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


async def _save_attachment(attachment: UploadFile | None) -> tuple[str, str, str | None, int] | None:
    if attachment is None or not attachment.filename:
        return None
    suffix = Path(attachment.filename).suffix.lower()
    if suffix not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的附件格式")

    settings.knowledge_storage_path.mkdir(parents=True, exist_ok=True)
    stored_path = settings.knowledge_storage_path / f"{uuid4().hex}{suffix}"
    size = 0
    try:
        with stored_path.open("wb") as target:
            while chunk := await attachment.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_knowledge_file_size_bytes:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="附件文件过大")
                target.write(chunk)
    except Exception:
        stored_path.unlink(missing_ok=True)
        raise

    return str(stored_path), attachment.filename, attachment.content_type, size


def _delete_attachment(path: str | None) -> None:
    if path:
        Path(path).unlink(missing_ok=True)


def _validate_text(db: Session, title: str, category: str, content: str, has_attachment: bool) -> tuple[str, str, str]:
    normalized_title = title.strip()
    normalized_category = category.strip()
    normalized_content = content.strip()
    if not normalized_title or not normalized_category:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请填写标题和分类")
    if not db.scalar(select(KnowledgeCategory.id).where(KnowledgeCategory.name == normalized_category)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="资料分类不存在，请先在分类设置中添加")
    if not normalized_content and not has_attachment:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="请填写正文或上传资料附件")
    return normalized_title, normalized_category, normalized_content


def _get_external_api_settings(db: Session) -> KnowledgeExternalApiSettings:
    config = db.get(KnowledgeExternalApiSettings, 1)
    if config:
        return config
    config = KnowledgeExternalApiSettings(id=1, is_enabled=False, api_key_hash="", api_key_prefix=None)
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def _external_api_response(
    config: KnowledgeExternalApiSettings, api_key: str | None = None
) -> KnowledgeExternalApiSettingsResponse:
    return KnowledgeExternalApiSettingsResponse(
        is_enabled=config.is_enabled,
        key_configured=bool(config.api_key_hash),
        api_key_prefix=config.api_key_prefix,
        api_key=api_key,
        updated_at=config.updated_at,
    )


@router.get("/categories", response_model=list[KnowledgeCategoryResponse])
def list_categories(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[KnowledgeCategory]:
    return db.scalars(select(KnowledgeCategory).order_by(KnowledgeCategory.name)).all()


@router.post("/categories", response_model=KnowledgeCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: KnowledgeCategoryCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> KnowledgeCategory:
    _require_admin(current_user)
    if db.scalar(select(KnowledgeCategory.id).where(KnowledgeCategory.name == payload.name)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="资料分类已存在")
    category = KnowledgeCategory(name=payload.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    _require_admin(current_user)
    category = db.get(KnowledgeCategory, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料分类不存在")
    entry_count = db.scalar(
        select(func.count()).select_from(KnowledgeEntry).where(KnowledgeEntry.category == category.name)
    ) or 0
    if entry_count:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该分类已有知识条目，不能删除")
    db.delete(category)
    db.commit()


@router.get("/external-api", response_model=KnowledgeExternalApiSettingsResponse)
def get_external_api_settings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> KnowledgeExternalApiSettingsResponse:
    _require_admin(current_user)
    return _external_api_response(_get_external_api_settings(db))


@router.put("/external-api", response_model=KnowledgeExternalApiSettingsResponse)
def update_external_api_settings(
    payload: KnowledgeExternalApiSettingsUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> KnowledgeExternalApiSettingsResponse:
    _require_admin(current_user)
    config = _get_external_api_settings(db)
    raw_api_key = None
    config.is_enabled = payload.is_enabled
    if not payload.is_enabled:
        config.api_key_hash = ""
        config.api_key_prefix = None
    elif payload.regenerate_key or not config.api_key_hash:
        raw_api_key = f"kb_{secrets.token_urlsafe(32)}"
        config.api_key_hash = hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()
        config.api_key_prefix = raw_api_key[:12]
    db.commit()
    db.refresh(config)
    return _external_api_response(config, raw_api_key)


@router.get("", response_model=KnowledgeListResponse)
def list_entries(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query("", max_length=255),
    category: str = Query("", max_length=64),
) -> KnowledgeListResponse:
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
def get_entry(
    entry_id: int,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> KnowledgeEntryResponse:
    return _response(_entry_or_404(db, entry_id))


@router.post("", response_model=KnowledgeEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    title: str = Form(...),
    category: str = Form(...),
    summary: str = Form(""),
    content: str = Form(""),
    attachment: UploadFile | None = File(default=None),
) -> KnowledgeEntryResponse:
    _require_admin(current_user)
    saved_attachment = await _save_attachment(attachment)
    normalized_title, normalized_category, normalized_content = _validate_text(
        db, title, category, content, saved_attachment is not None
    )
    entry = KnowledgeEntry(
        title=normalized_title,
        category=normalized_category,
        summary=summary.strip() or None,
        content=normalized_content,
        attachment_path=saved_attachment[0] if saved_attachment else None,
        attachment_name=saved_attachment[1] if saved_attachment else None,
        attachment_mime_type=saved_attachment[2] if saved_attachment else None,
        attachment_size=saved_attachment[3] if saved_attachment else None,
        created_by_id=current_user.id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _response(_entry_or_404(db, entry.id))


@router.put("/{entry_id}", response_model=KnowledgeEntryResponse)
async def update_entry(
    entry_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    title: str = Form(...),
    category: str = Form(...),
    summary: str = Form(""),
    content: str = Form(""),
    remove_attachment: bool = Form(False),
    attachment: UploadFile | None = File(default=None),
) -> KnowledgeEntryResponse:
    _require_admin(current_user)
    entry = _entry_or_404(db, entry_id)
    saved_attachment = await _save_attachment(attachment)
    keep_attachment = entry.attachment_path is not None and not remove_attachment and saved_attachment is None
    normalized_title, normalized_category, normalized_content = _validate_text(
        db, title, category, content, keep_attachment or saved_attachment is not None
    )
    old_path = entry.attachment_path
    entry.title = normalized_title
    entry.category = normalized_category
    entry.summary = summary.strip() or None
    entry.content = normalized_content
    if saved_attachment:
        entry.attachment_path = saved_attachment[0]
        entry.attachment_name = saved_attachment[1]
        entry.attachment_mime_type = saved_attachment[2]
        entry.attachment_size = saved_attachment[3]
    elif remove_attachment:
        entry.attachment_path = None
        entry.attachment_name = None
        entry.attachment_mime_type = None
        entry.attachment_size = None
    db.commit()
    if (saved_attachment or remove_attachment) and old_path != entry.attachment_path:
        _delete_attachment(old_path)
    return _response(_entry_or_404(db, entry.id))


@router.get("/{entry_id}/attachment")
def get_attachment(
    entry_id: int,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    entry = _entry_or_404(db, entry_id)
    if not entry.attachment_path or not Path(entry.attachment_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件不存在")
    return FileResponse(entry.attachment_path, media_type=entry.attachment_mime_type, filename=entry.attachment_name)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    _require_admin(current_user)
    entry = _entry_or_404(db, entry_id)
    attachment_path = entry.attachment_path
    db.delete(entry)
    db.commit()
    _delete_attachment(attachment_path)
