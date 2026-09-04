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
