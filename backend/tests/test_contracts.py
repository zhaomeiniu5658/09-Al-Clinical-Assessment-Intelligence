from app.models.assessment import ReviewStatus, ScaleType, TaskStage, TaskStatus


def test_enum_wire_values() -> None:
    assert ScaleType.HAMD.value == "HAMD"
    assert ScaleType.HAMA.value == "HAMA"
    assert ScaleType.PHQ9.value == "PHQ-9"
    assert TaskStatus.PENDING.value == "PENDING"
    assert TaskStage.ASR.value == "ASR"
    assert ReviewStatus.REVIEWED.value == "REVIEWED"

