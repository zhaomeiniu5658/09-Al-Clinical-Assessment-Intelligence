from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class XfyunAsrSettings(Base):
    __tablename__ = "xfyun_asr_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False, default="非实时语音转写大模型")
    app_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    api_secret: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    api_key: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    web_api: Mapped[str] = mapped_column(String(512), nullable=False, default="https://office-api-ist-dx.iflyaisol.com")
    hotwords: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
