from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.session import SessionLocal
from app.models.assessment import AssessmentTask, QcResult, TaskStage, TaskStatus
from app.models.system import XfyunAsrSettings
from app.services.ai_qc import DifyOpenAICompatibleQcService
from app.services.doctor_test import parse_doctor_test
from app.services.qc_items import merge_item_results
from app.services.xfyun_asr import XfyunAsrService


def process_assessment_task(task_id: int) -> None:
    db = SessionLocal()
    try:
        task = db.scalar(
            select(AssessmentTask)
            .options(joinedload(AssessmentTask.qc_result))
            .where(AssessmentTask.id == task_id)
        )
        if not task:
            return

        try:
            if not task.asr_text:
                task.status = TaskStatus.RUNNING
                task.stage = TaskStage.ASR
                task.error_message = None
                db.commit()

                xfyun_settings = db.get(XfyunAsrSettings, 1)
                task.asr_text = XfyunAsrService(xfyun_settings).transcribe(task.audio_path, task.audio_original_name)
                db.commit()

            task.status = TaskStatus.RUNNING
            task.stage = TaskStage.QC
            task.error_message = None
            db.commit()

            doctor_items = parse_doctor_test(task.doctor_test_path, task.scale_type) if task.doctor_test_path else []
            if doctor_items:
                doctor_total = sum(
                    row["doctor_score"]
                    for row in doctor_items
                    if isinstance(row.get("doctor_score"), int | float)
                )
                if task.qc_result:
                    task.qc_result.doctor_score = doctor_total
                    task.qc_result.item_results = merge_item_results(
                        doctor_items,
                        task.qc_result.item_results or [],
                    )
                else:
                    task.qc_result = QcResult(
                        doctor_score=doctor_total,
                        ai_score=None,
                        item_results=doctor_items,
                    )
                db.commit()

            result = DifyOpenAICompatibleQcService().run_qc(
                task.scale_type,
                task.asr_text or "",
                doctor_test_path=task.doctor_test_path,
            )
            merged_items = merge_item_results(
                doctor_items or result.item_results,
                result.item_results,
                assume_missing_ai_matches=bool(doctor_items),
            )
            if task.qc_result:
                qc_result = task.qc_result
                qc_result.doctor_score = result.doctor_score or qc_result.doctor_score
                qc_result.ai_score = result.ai_score
                qc_result.scoring_basis = result.scoring_basis
                qc_result.evidence_analysis = result.evidence_analysis
                qc_result.error_reason = result.error_reason
                qc_result.optimization_suggestion = result.optimization_suggestion
                qc_result.item_results = merged_items
                qc_result.raw_response = result.raw_response
            else:
                db.add(
                    QcResult(
                        task_id=task.id,
                        doctor_score=result.doctor_score,
                        ai_score=result.ai_score,
                        scoring_basis=result.scoring_basis,
                        evidence_analysis=result.evidence_analysis,
                        error_reason=result.error_reason,
                        optimization_suggestion=result.optimization_suggestion,
                        item_results=merged_items,
                        raw_response=result.raw_response,
                    )
                )

            task.status = TaskStatus.COMPLETED
            task.stage = None
            task.error_message = None
            db.commit()
        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
            db.commit()
            raise
    finally:
        db.close()
