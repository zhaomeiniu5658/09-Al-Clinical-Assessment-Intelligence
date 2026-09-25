from datetime import datetime

from pydantic import BaseModel, Field

from app.models.assessment import ReviewStatus, ScaleType, TaskStage, TaskStatus


class QcResultResponse(BaseModel):
    id: int
    doctor_score: float | None
    ai_score: float | None
    scoring_basis: str | None
    evidence_analysis: str | None
    error_reason: str | None
    optimization_suggestion: str | None
    item_results: list[dict] | None = None

    model_config = {"from_attributes": True}


class ReviewRecordResponse(BaseModel):
    id: int
    reviewed_score: float
    review_reason: str
    review_comment: str | None
    reviewed_at: datetime

    model_config = {"from_attributes": True}


class TaskListItem(BaseModel):
    id: int
    scale_type: ScaleType
    audio_original_name: str
    audio_mime_type: str | None
    audio_size: int
    status: TaskStatus
    stage: TaskStage | None
    review_status: ReviewStatus
    error_message: str | None
    asr_text: str | None
    doctor_score: float | None = None
    ai_score: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskDetailResponse(TaskListItem):
    qc_result: QcResultResponse | None = None
    review_record: ReviewRecordResponse | None = None


class TaskListResponse(BaseModel):
    items: list[TaskListItem]
    total: int
    page: int
    page_size: int


class ReviewCreate(BaseModel):
    reviewed_score: float = Field(..., ge=0)
    review_reason: str = Field(..., min_length=1, max_length=2000)
    review_comment: str | None = Field(default=None, max_length=5000)


class ItemReviewCreate(BaseModel):
    review_score: float = Field(..., ge=0)
    review_opinion: str = Field(..., min_length=1, max_length=2000)
