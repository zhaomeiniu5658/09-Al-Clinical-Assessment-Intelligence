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
    raw_response: dict[str, Any]


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
                        "根据医患对话文本完成量表质控：提炼医生评分，给出AI评分、评分依据、"
                        "证据分析、错误原因和优化建议。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"量表类型：{scale_type.value}\n\n"
                        f"医患对话转录文本：\n{dialogue_text}\n\n"
                        "请返回 JSON 字段：doctor_score, ai_score, scoring_basis, "
                        "evidence_analysis, error_reason, optimization_suggestion。"
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
        return AiQcResult(
            doctor_score=self._to_float(output.get("doctor_score")),
            ai_score=self._to_float(output.get("ai_score")),
            scoring_basis=self._to_text(output.get("scoring_basis")),
            evidence_analysis=self._to_text(output.get("evidence_analysis")),
            error_reason=self._to_text(output.get("error_reason")),
            optimization_suggestion=self._to_text(output.get("optimization_suggestion")),
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
