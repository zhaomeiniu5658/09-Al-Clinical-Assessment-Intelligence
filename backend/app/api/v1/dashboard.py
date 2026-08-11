from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.assessment import AssessmentTask, ReviewStatus, TaskStatus
from app.models.user import User
from app.schemas.dashboard import DashboardOverviewResponse, DashboardRecentTask

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_overview(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DashboardOverviewResponse:
    base_filter = AssessmentTask.owner_id == current_user.id

    def count_tasks(*conditions: object) -> int:
        return db.scalar(select(func.count()).select_from(AssessmentTask).where(base_filter, *conditions)) or 0

    recent_tasks = db.scalars(
        select(AssessmentTask)
        .options(joinedload(AssessmentTask.qc_result))
        .where(base_filter)
        .order_by(AssessmentTask.created_at.desc())
        .limit(6)
    ).all()
    return DashboardOverviewResponse(
        total_tasks=count_tasks(),
        pending_tasks=count_tasks(AssessmentTask.status == TaskStatus.PENDING),
        running_tasks=count_tasks(AssessmentTask.status == TaskStatus.RUNNING),
        completed_tasks=count_tasks(AssessmentTask.status == TaskStatus.COMPLETED),
        failed_tasks=count_tasks(AssessmentTask.status == TaskStatus.FAILED),
        reviewed_tasks=count_tasks(AssessmentTask.review_status == ReviewStatus.REVIEWED),
        recent_tasks=[
            DashboardRecentTask(
                id=task.id,
                scale_type=task.scale_type,
                audio_original_name=task.audio_original_name,
                status=task.status,
                stage=task.stage,
                review_status=task.review_status,
                ai_score=task.qc_result.ai_score if task.qc_result else None,
                created_at=task.created_at,
            )
            for task in recent_tasks
        ],
    )
