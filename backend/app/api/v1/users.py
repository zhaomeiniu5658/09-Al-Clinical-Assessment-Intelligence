from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.assessment import AssessmentTask
from app.models.knowledge import KnowledgeEntry
from app.models.user import User
from app.schemas.user import ManagedUserResponse, UserCreate, UserListResponse, UserStatusUpdate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _require_admin(current_user: User) -> None:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可以管理用户")


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user


@router.get("", response_model=UserListResponse)
def list_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: str = Query("", max_length=64),
    is_active: bool | None = Query(default=None),
) -> UserListResponse:
    _require_admin(current_user)
    statement = select(User)
    if keyword.strip():
        statement = statement.where(User.username.ilike(f"%{keyword.strip()}%"))
    if is_active is not None:
        statement = statement.where(User.is_active == is_active)

    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    users = db.scalars(
        statement.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return UserListResponse(items=users, total=total, page=page, page_size=page_size)


@router.post("", response_model=ManagedUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    _require_admin(current_user)
    if db.scalar(select(User.id).where(User.username == payload.username)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")

    user = User(username=payload.username, hashed_password=get_password_hash(payload.password), is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=ManagedUserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    _require_admin(current_user)
    user = _get_user_or_404(db, user_id)
    if payload.username is not None and payload.username != user.username:
        if db.scalar(select(User.id).where(User.username == payload.username, User.id != user.id)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")
        user.username = payload.username
    if payload.password is not None:
        user.hashed_password = get_password_hash(payload.password)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/status", response_model=ManagedUserResponse)
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    _require_admin(current_user)
    user = _get_user_or_404(db, user_id)
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能停用自己的账户")
    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    _require_admin(current_user)
    user = _get_user_or_404(db, user_id)
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己的账户")
    task_count = db.scalar(select(func.count()).select_from(AssessmentTask).where(AssessmentTask.owner_id == user.id)) or 0
    if task_count:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该用户已有质控任务，不能删除")
    knowledge_count = db.scalar(
        select(func.count()).select_from(KnowledgeEntry).where(KnowledgeEntry.created_by_id == user.id)
    ) or 0
    if knowledge_count:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该用户已有知识库条目，不能删除")
    db.delete(user)
    db.commit()
