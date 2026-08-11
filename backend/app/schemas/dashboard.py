from datetime import datetime

from pydantic import BaseModel

from app.models.assessment import ReviewStatus, ScaleType, TaskStage, TaskStatus


class DashboardRecentTask(BaseModel):
    id: int
    scale_type: ScaleType
    audio_original_name: str
    status: TaskStatus
    stage: TaskStage | None
    review_status: ReviewStatus
    ai_score: float | None
    created_at: datetime


class DashboardOverviewResponse(BaseModel):
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    reviewed_tasks: int
    recent_tasks: list[DashboardRecentTask]
