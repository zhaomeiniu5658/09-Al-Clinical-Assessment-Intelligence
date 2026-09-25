from contextlib import suppress
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.assessment import AssessmentTask, QcResult, ReviewRecord, ReviewStatus, ScaleType, TaskStatus
from app.models.user import User
from app.schemas.task import ItemReviewCreate, ReviewCreate, TaskDetailResponse, TaskListItem, TaskListResponse
from app.services.doctor_test import parse_doctor_test
from app.tasks.worker import process_assessment_task

router = APIRouter(prefix="/tasks", tags=["tasks"])

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".opus", ".m4a"}
ALLOWED_DOCTOR_TEST_EXTENSIONS = {".xls", ".xlsx"}


def _task_to_list_item(task: AssessmentTask) -> TaskListItem:
    return TaskListItem(
        id=task.id,
        scale_type=task.scale_type,
        audio_original_name=task.audio_original_name,
        audio_mime_type=task.audio_mime_type,
        audio_size=task.audio_size,
        status=task.status,
        stage=task.stage,
        review_status=task.review_status,
        error_message=task.error_message,
        asr_text=task.asr_text,
        doctor_score=task.qc_result.doctor_score if task.qc_result else None,
        ai_score=task.qc_result.ai_score if task.qc_result else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post("", response_model=TaskDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    scale_type: ScaleType = Form(...),
    audio_file: UploadFile = File(...),
    doctor_test_file: UploadFile | None = File(None),
) -> AssessmentTask:
    if (
        settings.dify_protocol.lower() == "workflow"
    ):
        if scale_type != ScaleType.HAMD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前远程 Dify Workflow 仅支持 HAMD（HAM-D17），HAMA 和 PHQ-9 暂不可提交",
            )
        if settings.dify_workflow_require_doctor_test_file and not doctor_test_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前 Dify Workflow 要求上传医生打分表，请使用 doctor_test_file 字段提交",
            )
        if settings.dify_workflow_require_doctor_test_file and doctor_test_file and not doctor_test_file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="医生打分表不能为空，请重新选择 Excel 文件",
            )

    suffix = Path(audio_file.filename or "").suffix.lower()
    if suffix not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的音频格式")

    settings.audio_storage_path.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{suffix}"
    audio_path = settings.audio_storage_path / stored_name

    size = 0
    with audio_path.open("wb") as target:
        while chunk := await audio_file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_audio_size_bytes:
                target.close()
                audio_path.unlink(missing_ok=True)
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="音频文件过大")
            target.write(chunk)

    doctor_test_path: Path | None = None
    doctor_test_size: int | None = None
    doctor_test_original_name: str | None = None
    doctor_test_mime_type: str | None = None
    if doctor_test_file and doctor_test_file.filename:
        doctor_test_suffix = Path(doctor_test_file.filename).suffix.lower()
        if doctor_test_suffix not in ALLOWED_DOCTOR_TEST_EXTENSIONS:
            audio_path.unlink(missing_ok=True)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="医生打分表仅支持 Excel 格式（.xls 或 .xlsx）")

        doctor_test_storage_path = settings.storage_path / "doctor_tests"
        doctor_test_storage_path.mkdir(parents=True, exist_ok=True)
        doctor_test_path = doctor_test_storage_path / f"{uuid4().hex}{doctor_test_suffix}"
        doctor_test_size = 0
        with doctor_test_path.open("wb") as target:
            while chunk := await doctor_test_file.read(1024 * 1024):
                doctor_test_size += len(chunk)
                if doctor_test_size > settings.max_knowledge_file_size_bytes:
                    target.close()
                    doctor_test_path.unlink(missing_ok=True)
                    audio_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="医生打分表文件过大",
                    )
                target.write(chunk)
        doctor_test_original_name = doctor_test_file.filename
        doctor_test_mime_type = doctor_test_file.content_type

    initial_item_results: list[dict] | None = None
    initial_doctor_score: float | None = None
    if doctor_test_path and scale_type == ScaleType.HAMD:
        try:
            initial_item_results = parse_doctor_test(doctor_test_path, scale_type)
            initial_doctor_score = sum(
                row["doctor_score"]
                for row in initial_item_results
                if isinstance(row.get("doctor_score"), int | float)
            )
        except Exception as exc:
            doctor_test_path.unlink(missing_ok=True)
            audio_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"医生打分表解析失败：{exc}",
            ) from exc

    task = AssessmentTask(
        owner_id=current_user.id,
        scale_type=scale_type,
        audio_path=str(audio_path),
        audio_original_name=audio_file.filename or stored_name,
        audio_mime_type=audio_file.content_type,
        audio_size=size,
        doctor_test_path=str(doctor_test_path) if doctor_test_path else None,
        doctor_test_original_name=doctor_test_original_name,
        doctor_test_mime_type=doctor_test_mime_type,
        doctor_test_size=doctor_test_size,
        status=TaskStatus.PENDING,
        review_status=ReviewStatus.UNREVIEWED,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    if initial_item_results is not None:
        task.qc_result = QcResult(
            doctor_score=initial_doctor_score,
            ai_score=None,
            item_results=initial_item_results,
        )
        db.commit()
        db.refresh(task)

    background_tasks.add_task(process_assessment_task, task.id)
    return task


@router.get("", response_model=TaskListResponse)
def list_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> TaskListResponse:
    base = select(AssessmentTask).where(AssessmentTask.owner_id == current_user.id)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    tasks = db.scalars(
        base.options(joinedload(AssessmentTask.qc_result))
        .order_by(AssessmentTask.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return TaskListResponse(
        items=[_task_to_list_item(task) for task in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AssessmentTask:
    task = db.scalar(
        select(AssessmentTask)
        .options(joinedload(AssessmentTask.qc_result), joinedload(AssessmentTask.review_record))
        .where(AssessmentTask.id == task_id, AssessmentTask.owner_id == current_user.id)
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task


@router.get("/{task_id}/audio")
def get_audio(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    task = db.scalar(select(AssessmentTask).where(AssessmentTask.id == task_id, AssessmentTask.owner_id == current_user.id))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    path = Path(task.audio_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="音频文件不存在")
    return FileResponse(path, media_type=task.audio_mime_type, filename=task.audio_original_name)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    task = db.scalar(
        select(AssessmentTask)
        .options(joinedload(AssessmentTask.qc_result), joinedload(AssessmentTask.review_record))
        .where(AssessmentTask.id == task_id, AssessmentTask.owner_id == current_user.id)
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    file_paths = [task.audio_path, task.doctor_test_path]
    db.delete(task)
    db.commit()
    for file_path in file_paths:
        if file_path:
            with suppress(FileNotFoundError):
                Path(file_path).unlink()


@router.post("/{task_id}/retry", response_model=TaskDetailResponse)
def retry_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AssessmentTask:
    task = db.scalar(
        select(AssessmentTask)
        .options(joinedload(AssessmentTask.qc_result), joinedload(AssessmentTask.review_record))
        .where(AssessmentTask.id == task_id, AssessmentTask.owner_id == current_user.id)
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    if task.status != TaskStatus.FAILED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅失败任务可重试")

    task.status = TaskStatus.PENDING
    task.stage = None
    task.error_message = None
    db.commit()
    db.refresh(task)
    background_tasks.add_task(process_assessment_task, task.id)
    return task


@router.post("/{task_id}/review", response_model=TaskDetailResponse)
def review_task(
    task_id: int,
    payload: ReviewCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AssessmentTask:
    task = db.scalar(
        select(AssessmentTask)
        .options(joinedload(AssessmentTask.qc_result), joinedload(AssessmentTask.review_record))
        .where(AssessmentTask.id == task_id, AssessmentTask.owner_id == current_user.id)
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="任务完成后才能审核")

    if task.review_record:
        task.review_record.reviewed_score = payload.reviewed_score
        task.review_record.review_reason = payload.review_reason
        task.review_record.review_comment = payload.review_comment
    else:
        db.add(
            ReviewRecord(
                task_id=task.id,
                reviewed_score=payload.reviewed_score,
                review_reason=payload.review_reason,
                review_comment=payload.review_comment,
            )
        )
    task.review_status = ReviewStatus.REVIEWED
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/items/{item_index}/review", response_model=TaskDetailResponse)
def review_task_item(
    task_id: int,
    item_index: int,
    payload: ItemReviewCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AssessmentTask:
    task = db.scalar(
        select(AssessmentTask)
        .options(joinedload(AssessmentTask.qc_result), joinedload(AssessmentTask.review_record))
        .where(AssessmentTask.id == task_id, AssessmentTask.owner_id == current_user.id)
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    if not task.qc_result or not task.qc_result.item_results:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="暂无可复核的量表项目")
    if item_index < 0 or item_index >= len(task.qc_result.item_results):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="量表项目不存在")

    item_results = [dict(item) for item in task.qc_result.item_results]
    item_results[item_index]["review_score"] = payload.review_score
    item_results[item_index]["review_opinion"] = payload.review_opinion
    task.qc_result.item_results = item_results
    db.commit()
    db.refresh(task)
    return task
