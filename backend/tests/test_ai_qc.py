from app.services.ai_qc import DifyOpenAICompatibleQcService


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
