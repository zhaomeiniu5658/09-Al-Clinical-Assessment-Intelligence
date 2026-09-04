import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings
from app.models.assessment import ScaleType


@dataclass
class AiQcResult:
    doctor_score: float | None
    ai_score: float | None
    scoring_basis: str | None
    evidence_analysis: str | None
    error_reason: str | None
    optimization_suggestion: str | None
    item_results: list[dict[str, Any]]
    raw_response: dict[str, Any]


HAMD17_ITEMS = [
    "1.抑郁情绪（悲伤、无望、无助、无价值）",
    "2.有罪感",
    "3.自杀",
    "4.入睡困难",
    "5.睡眠不深",
    "6.早醒",
    "7.工作和活动",
    "8.迟滞（指思维和言语缓慢，注意力难以集中，主动性减退）；",
    "9.激越",
    "10.精神性焦虑",
    "11.躯体性焦虑（焦虑的生理症状，如口干、气促、消化不良、腹泻、腹部绞痛、嗳气、心悸、头痛、过度换气、叹气、尿频、出汗）",
    "12.胃肠道症状",
    "13.全身症状",
    "14.性症状（性欲丧失、月经失调）",
    "15.疑病",
    "16.体重减轻",
    "17.自知力",
]


class DifyOpenAICompatibleQcService:
    """Dify app client through an OpenAI-compatible Chat Completions protocol."""

    def __init__(self) -> None:
        self.base_url = settings.dify_openai_base_url.rstrip("/")
        self.timeout = settings.dify_timeout_seconds

    def run_qc(self, scale_type: ScaleType, dialogue_text: str) -> AiQcResult:
        api_key = self._api_key_for_scale(scale_type)
        if not api_key:
            raise RuntimeError(f"未配置 {scale_type.value} 对应的 Dify API Key")

        payload = {
            "model": settings.dify_openai_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是临床量表质控专家。请只输出 JSON，不要输出 Markdown。"
                        "根据医患对话文本完成量表质控：提炼评分员打分，给出AI打分和AI打分依据。"
                        "最终结果必须包含逐项目质控明细。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"量表类型：{scale_type.value}\n\n"
                        f"医患对话转录文本：\n{dialogue_text}\n\n"
                        f"HAM-D17项目清单：\n{json.dumps(HAMD17_ITEMS, ensure_ascii=False)}\n\n"
                        "请返回 JSON 字段：doctor_score, ai_score, scoring_basis, "
                        "evidence_analysis, error_reason, optimization_suggestion, item_results。"
                        "其中 item_results 必须是数组，每一项包含："
                        "hamd_item（HAM-D17项目原文）, doctor_score（评分员打分）, "
                        "ai_score（AI打分）, ai_scoring_basis（AI打分依据，引用对话证据并说明评分原因）。"
                    ),
                },
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            raw = response.json()

        output = self._extract_json_content(raw)
        item_results = self._normalize_item_results(output.get("item_results"))
        doctor_score = self._to_float(output.get("doctor_score"))
        ai_score = self._to_float(output.get("ai_score"))
        return AiQcResult(
            doctor_score=doctor_score if doctor_score is not None else self._score_from_items(item_results, "doctor_score"),
            ai_score=ai_score if ai_score is not None else self._score_from_items(item_results, "ai_score"),
            scoring_basis=self._to_text(output.get("scoring_basis")),
            evidence_analysis=self._to_text(output.get("evidence_analysis")),
            error_reason=self._to_text(output.get("error_reason")),
            optimization_suggestion=self._to_text(output.get("optimization_suggestion")),
            item_results=item_results,
            raw_response=raw,
        )

    def _api_key_for_scale(self, scale_type: ScaleType) -> str:
        return {
            ScaleType.HAMD: settings.dify_hamd_api_key,
            ScaleType.HAMA: settings.dify_hama_api_key,
            ScaleType.PHQ9: settings.dify_phq9_api_key,
        }[scale_type]

    @staticmethod
    def _extract_json_content(raw: dict[str, Any]) -> dict[str, Any]:
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("OpenAI 兼容响应缺少 choices")

        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"
            )
        if not isinstance(content, str) or not content.strip():
            raise ValueError("OpenAI 兼容响应缺少 message.content")

        normalized = content.strip()
        if normalized.startswith("```"):
            normalized = normalized.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            parsed = json.loads(normalized)
        except json.JSONDecodeError as exc:
            raise ValueError("AI 质控输出不是有效 JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("AI 质控输出 JSON 必须是对象")
        return parsed

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None or value == "":
            return None
        return float(value)

    @staticmethod
    def _to_text(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)

    @classmethod
    def _normalize_item_results(cls, value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []

        normalized: list[dict[str, Any]] = []
        for index, row in enumerate(value):
            if not isinstance(row, dict):
                continue
            item = cls._first_value(row, "hamd_item", "HAM-D17项目", "item", "project", "name", "项目")
            normalized.append(
                {
                    "hamd_item": cls._to_text(item) or (HAMD17_ITEMS[index] if index < len(HAMD17_ITEMS) else ""),
                    "doctor_score": cls._to_float_or_none(
                        cls._first_value(row, "doctor_score", "评分员打分", "rater_score", "clinician_score", "医生评分")
                    ),
                    "ai_score": cls._to_float_or_none(cls._first_value(row, "ai_score", "AI打分", "ai评分", "标准分")),
                    "ai_scoring_basis": cls._to_text(
                        cls._first_value(row, "ai_scoring_basis", "AI打分依据", "scoring_basis", "basis", "依据")
                    ),
                }
            )
        return normalized

    @staticmethod
    def _first_value(row: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in row:
                return row[key]
        return None

    @staticmethod
    def _to_float_or_none(value: Any) -> float | None:
        try:
            return DifyOpenAICompatibleQcService._to_float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _score_from_items(item_results: list[dict[str, Any]], key: str) -> float | None:
        scores = [row.get(key) for row in item_results if isinstance(row.get(key), int | float)]
        return float(sum(scores)) if scores else None
