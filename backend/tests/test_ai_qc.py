from app.services.ai_qc import DifyOpenAICompatibleQcService
from app.services.qc_items import merge_item_results


def test_normalize_item_results_accepts_chinese_headers() -> None:
    rows = DifyOpenAICompatibleQcService._normalize_item_results(
        [
            {
                "HAM-D17项目": "1.抑郁情绪（悲伤、无望、无助、无价值）",
                "评分员打分": "3",
                "AI打分": 2,
                "AI打分依据": "访谈中出现悲伤和无望相关表达。",
            }
        ]
    )

    assert rows == [
        {
            "hamd_item": "1.抑郁情绪（悲伤、无望、无助、无价值）",
            "doctor_score": 3.0,
            "ai_score": 2.0,
            "ai_scoring_basis": "访谈中出现悲伤和无望相关表达。",
        }
    ]


def test_extract_workflow_json_reads_dify_outputs_text() -> None:
    output, content = DifyOpenAICompatibleQcService._extract_workflow_json(
        {
            "data": {
                "status": "succeeded",
                "outputs": {
                    "text": '{"doctor_total_score": 18, "ai_total_score": 20, "differences": []}',
                },
            }
        }
    )

    assert output == {"doctor_total_score": 18, "ai_total_score": 20, "differences": []}
    assert content.startswith('{"doctor_total_score"')


def test_workflow_output_maps_totals_and_difference_rows() -> None:
    result = DifyOpenAICompatibleQcService._result_from_output(
        {
            "doctor_total_score": 18,
            "ai_total_score": 20,
            "difference_count": 1,
            "differences": [
                {
                    "item": 1,
                    "name": "抑郁情绪",
                    "doctor_score": 1,
                    "ai_score": 2,
                    "ai_scoring_basis": "患者自述持续悲伤。",
                    "difference_reason": "现有证据不足以支持更高评分。",
                }
            ],
        },
        {"data": {"outputs": {}}},
    )

    assert result.doctor_score == 18
    assert result.ai_score == 20
    assert result.item_results[0]["hamd_item"] == "抑郁情绪"
    assert "差异原因" in result.item_results[0]["ai_scoring_basis"]
    assert result.optimization_suggestion == "请针对差异项目进行人工复核"


def test_workflow_output_maps_item_number_and_name() -> None:
    result = DifyOpenAICompatibleQcService._result_from_output(
        {
            "differences": [
                {
                    "item": 1,
                    "name": "抑郁情绪",
                    "ai_score": 2,
                    "ai_scoring_basis": "患者自述持续悲伤。",
                }
            ],
        },
        {"data": {"outputs": {}}},
    )

    assert result.item_results[0]["hamd_item"] == "抑郁情绪"
    assert result.item_results[0]["ai_score"] == 2
    assert result.item_results[0]["ai_scoring_basis"] == "患者自述持续悲伤。"


def test_text_table_output_is_parsed_into_item_results() -> None:
    output, _ = DifyOpenAICompatibleQcService._extract_workflow_json(
        {
            "data": {
                "status": "succeeded",
                "outputs": {
                    "text": (
                        "项目编号 | 项目名称 | 医生打分 | AI评分 | AI评分依据 | 差异\n"
                        "1 | 抑郁情绪 | 3 | 2 | 患者主动描述状态不是很好。 | 1\n"
                    ),
                },
            }
        }
    )

    result = DifyOpenAICompatibleQcService._result_from_output(output, {"data": {}})
    assert result.item_results[0]["doctor_score"] == 3
    assert result.item_results[0]["ai_score"] == 2
    assert result.item_results[0]["difference"] == 1


def test_merge_item_results_keeps_complete_doctor_sheet() -> None:
    doctor_items = [
        {"hamd_item": "1.抑郁情绪", "doctor_score": 3},
        {"hamd_item": "2.有罪感", "doctor_score": 1},
    ]
    ai_items = [
        {"hamd_item": "1.抑郁情绪", "ai_score": 2, "ai_scoring_basis": "患者持续悲伤。"},
    ]

    rows = merge_item_results(doctor_items, ai_items, assume_missing_ai_matches=True)
    assert rows == [
        {
            "hamd_item": "1.抑郁情绪",
            "doctor_score": 3,
            "ai_score": 2,
            "ai_scoring_basis": "患者持续悲伤。",
            "difference": 1,
        },
        {
            "hamd_item": "2.有罪感",
            "doctor_score": 1,
            "ai_score": 1,
            "ai_scoring_basis": None,
            "difference": 0,
        },
    ]
