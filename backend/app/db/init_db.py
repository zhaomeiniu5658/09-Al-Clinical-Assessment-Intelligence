from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User


def init_single_admin(db: Session) -> User:
    user = db.scalar(select(User).where(User.username == settings.admin_username))
    if user:
        if not user.is_admin:
            user.is_admin = True
            db.commit()
        return user

    user = User(
        username=settings.admin_username,
        hashed_password=get_password_hash(settings.admin_password),
        is_active=True,
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

