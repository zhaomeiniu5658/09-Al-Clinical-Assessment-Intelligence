from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ScaleType(str, Enum):
    HAMD = "HAMD"
    HAMA = "HAMA"
    PHQ9 = "PHQ-9"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TaskStage(str, Enum):
    ASR = "ASR"
    QC = "QC"


class ReviewStatus(str, Enum):
    UNREVIEWED = "UNREVIEWED"
    REVIEWED = "REVIEWED"


class AssessmentTask(Base):
    __tablename__ = "assessment_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    scale_type: Mapped[ScaleType] = mapped_column(SAEnum(ScaleType), nullable=False, index=True)
    audio_path: Mapped[str] = mapped_column(String(512), nullable=False)
    audio_original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    audio_mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    audio_size: Mapped[int] = mapped_column(Integer, nullable=False)
    asr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(SAEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    stage: Mapped[TaskStage | None] = mapped_column(SAEnum(TaskStage), nullable=True)
    review_status: Mapped[ReviewStatus] = mapped_column(
        SAEnum(ReviewStatus), default=ReviewStatus.UNREVIEWED, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    owner = relationship("User", back_populates="tasks")
    qc_result = relationship("QcResult", back_populates="task", uselist=False, cascade="all, delete-orphan")
    review_record = relationship(
        "ReviewRecord", back_populates="task", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def doctor_score(self) -> float | None:
        return self.qc_result.doctor_score if self.qc_result else None

    @property
    def ai_score(self) -> float | None:
        return self.qc_result.ai_score if self.qc_result else None


class QcResult(Base):
    __tablename__ = "qc_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("assessment_tasks.id"), unique=True, nullable=False)
    doctor_score: Mapped[float | None] = mapped_column(nullable=True)
    ai_score: Mapped[float | None] = mapped_column(nullable=True)
    scoring_basis: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    optimization_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    task = relationship("AssessmentTask", back_populates="qc_result")


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("assessment_tasks.id"), unique=True, nullable=False)
    reviewed_score: Mapped[float] = mapped_column(nullable=False)
    review_reason: Mapped[str] = mapped_column(Text, nullable=False)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    task = relationship("AssessmentTask", back_populates="review_record")
