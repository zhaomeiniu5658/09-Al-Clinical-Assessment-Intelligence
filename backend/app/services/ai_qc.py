import json
import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings
from app.models.assessment import ScaleType
from app.services.doctor_test import HAMD17_ITEMS


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


class DifyOpenAICompatibleQcService:
    """Dify client supporting both Workflow and OpenAI-compatible app APIs."""

    def __init__(self) -> None:
        self.openai_base_url = settings.dify_openai_base_url.rstrip("/")
        self.workflow_base_url = settings.dify_workflow_base_url.rstrip("/")
        self.timeout = settings.dify_timeout_seconds

    def run_qc(
        self,
        scale_type: ScaleType,
        dialogue_text: str,
        doctor_test_path: str | Path | None = None,
    ) -> AiQcResult:
        if settings.dify_protocol.lower() == "workflow":
            return self._run_workflow(scale_type, dialogue_text, doctor_test_path)
        return self._run_openai_compatible(scale_type, dialogue_text)

    def _run_workflow(
        self,
        scale_type: ScaleType,
        dialogue_text: str,
        doctor_test_path: str | Path | None,
    ) -> AiQcResult:
        if scale_type != ScaleType.HAMD:
            raise RuntimeError("当前远程 Dify 工作流仅支持 HAMD（HAM-D17），HAMA 和 PHQ-9 需配置独立应用")

        api_key = settings.dify_workflow_api_key or self._api_key_for_scale(scale_type)
        if not api_key:
            raise RuntimeError("未配置 Dify Workflow API Key，请设置 DIFY_WORKFLOW_API_KEY")

        with httpx.Client(timeout=self.timeout) as client:
            inputs: dict[str, Any] = {
                settings.dify_workflow_dialog_input: dialogue_text,
            }
            if doctor_test_path:
                upload_file_id = self._upload_workflow_file(client, Path(doctor_test_path), api_key)
                inputs[settings.dify_workflow_doctor_test_input] = {
                    "type": "document",
                    "transfer_method": "local_file",
                    "upload_file_id": upload_file_id,
                }

            response = client.post(
                f"{self.workflow_base_url}/v1/workflows/run",
                headers=self._headers(api_key),
                json={
                    "inputs": inputs,
                    "response_mode": "blocking",
                    "user": settings.dify_workflow_user,
                },
            )
            self._raise_for_dify(response, "Workflow")
            raw = response.json()

        output, content = self._extract_workflow_json(raw)
        return self._result_from_output(output, raw, content)

    def _run_openai_compatible(self, scale_type: ScaleType, dialogue_text: str) -> AiQcResult:
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
                f"{self.openai_base_url}/v1/chat/completions",
                headers=self._headers(api_key),
                json=payload,
            )
            self._raise_for_dify(response, "OpenAI 兼容")
            raw = response.json()

        output = self._extract_json_content(raw)
        return self._result_from_output(output, raw)

    def _upload_workflow_file(self, client: httpx.Client, path: Path, api_key: str) -> str:
        if not path.exists() or not path.is_file():
            raise RuntimeError("医生打分表文件不存在")

        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        with path.open("rb") as file:
            response = client.post(
                f"{self.workflow_base_url}/v1/files/upload",
                headers={"Authorization": f"Bearer {api_key}"},
                data={"user": settings.dify_workflow_user},
                files={"file": (path.name, file, mime_type)},
            )
        self._raise_for_dify(response, "Workflow 文件上传")
        upload = response.json()
        upload_file_id = upload.get("id")
        if not isinstance(upload_file_id, str) or not upload_file_id:
            raise ValueError("Dify 文件上传响应缺少文件 ID")
        return upload_file_id

    def _api_key_for_scale(self, scale_type: ScaleType) -> str:
        return {
            ScaleType.HAMD: settings.dify_hamd_api_key,
            ScaleType.HAMA: settings.dify_hama_api_key,
            ScaleType.PHQ9: settings.dify_phq9_api_key,
        }[scale_type]

    @staticmethod
    def _headers(api_key: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    @staticmethod
    def _raise_for_dify(response: httpx.Response, operation: str) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = ""
            try:
                body = response.json()
                if isinstance(body, dict):
                    detail = str(body.get("message") or body.get("error") or "").strip()
            except ValueError:
                detail = response.text.strip()
            suffix = f": {detail}" if detail else ""
            raise RuntimeError(f"Dify {operation} 请求失败（HTTP {response.status_code}）{suffix}") from exc

    @classmethod
    def _result_from_output(
        cls,
        output: dict[str, Any],
        raw_response: dict[str, Any],
        content: str | None = None,
    ) -> AiQcResult:
        item_value = output.get("item_results") or output.get("items") or output.get("differences")
        item_results = cls._normalize_item_results(item_value)

        doctor_score = cls._first_number(output, "doctor_score", "doctor_total_score")
        ai_score = cls._first_number(output, "ai_score", "ai_total_score")
        difference_count = output.get("difference_count")
        if difference_count is None and output.get("differences") is not None:
            difference_count = len(output["differences"]) if isinstance(output["differences"], list) else None

        scoring_basis = cls._to_text(output.get("scoring_basis"))
        evidence_analysis = cls._to_text(output.get("evidence_analysis"))
        error_reason = cls._to_text(output.get("error_reason"))
        optimization_suggestion = cls._to_text(output.get("optimization_suggestion"))

        if content and not evidence_analysis:
            evidence_analysis = content
        if difference_count is not None and not error_reason:
            error_reason = f"Dify 工作流识别到 {difference_count} 项评分差异"
        if difference_count is not None and not optimization_suggestion:
            optimization_suggestion = "请针对差异项目进行人工复核" if difference_count else "未发现评分差异"

        return AiQcResult(
            doctor_score=doctor_score if doctor_score is not None else cls._score_from_items(item_results, "doctor_score"),
            ai_score=ai_score if ai_score is not None else cls._score_from_items(item_results, "ai_score"),
            scoring_basis=scoring_basis,
            evidence_analysis=evidence_analysis,
            error_reason=error_reason,
            optimization_suggestion=optimization_suggestion,
            item_results=item_results,
            raw_response=raw_response,
        )

    @classmethod
    def _extract_workflow_json(cls, raw: dict[str, Any]) -> tuple[dict[str, Any], str]:
        data = raw.get("data")
        if not isinstance(data, dict):
            raise ValueError("Dify Workflow 响应缺少 data")
        if data.get("status") and data.get("status") != "succeeded":
            error = data.get("error") or "工作流未成功完成"
            raise RuntimeError(f"Dify Workflow 执行失败：{error}")

        outputs = data.get("outputs")
        if not isinstance(outputs, dict):
            raise ValueError("Dify Workflow 响应缺少 data.outputs")

        content: Any = outputs.get("text")
        if content is None:
            for key in ("result", "output", "answer"):
                if outputs.get(key) is not None:
                    content = outputs[key]
                    break
        if isinstance(content, dict):
            return content, json.dumps(content, ensure_ascii=False)
        if not isinstance(content, str) or not content.strip():
            string_values = [value for value in outputs.values() if isinstance(value, str) and value.strip()]
            content = string_values[0] if string_values else None
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Dify Workflow 响应缺少可解析的输出文本")
        try:
            return cls._parse_json_object(content), content.strip()
        except ValueError:
            table_rows = cls._parse_text_table(content)
            if not table_rows:
                raise
            return {"item_results": table_rows, "evidence_analysis": content.strip()}, content.strip()

    @classmethod
    def _extract_json_content(cls, raw: dict[str, Any]) -> dict[str, Any]:
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
        return cls._parse_json_object(content)

    @staticmethod
    def _parse_json_object(content: str) -> dict[str, Any]:
        normalized = content.strip()
        if normalized.startswith("```"):
            normalized = normalized.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            parsed = json.loads(normalized)
        except json.JSONDecodeError:
            start = normalized.find("{")
            end = normalized.rfind("}")
            if start < 0 or end <= start:
                raise ValueError("AI 质控输出不是有效 JSON")
            try:
                parsed = json.loads(normalized[start : end + 1])
            except json.JSONDecodeError as exc:
                raise ValueError("AI 质控输出不是有效 JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("AI 质控输出 JSON 必须是对象")
        return parsed

    @classmethod
    def _normalize_item_results(cls, value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []

        normalized: list[dict[str, Any]] = []
        for index, row in enumerate(value):
            if not isinstance(row, dict):
                continue
            item_number = cls._to_float_or_none(
                cls._first_value(row, "item_number", "item", "项目编号", "编号")
            )
            item = cls._first_value(row, "hamd_item", "HAM-D17项目", "name", "project", "项目")
            item_text = cls._to_text(item)
            if not item_text and isinstance(item_number, int | float):
                number = int(item_number)
                item_text = HAMD17_ITEMS[number - 1] if 1 <= number <= len(HAMD17_ITEMS) else str(number)
            basis = cls._first_value(
                row,
                "ai_scoring_basis",
                "AI打分依据",
                "scoring_basis",
                "basis",
                "依据",
                "evidence",
            )
            difference_reason = cls._to_text(row.get("difference_reason"))
            if difference_reason:
                basis = f"{cls._to_text(basis) or ''}\n差异原因：{difference_reason}".strip()
            normalized_row = {
                "hamd_item": item_text or (HAMD17_ITEMS[index] if index < len(HAMD17_ITEMS) else ""),
                "doctor_score": cls._to_float_or_none(
                    cls._first_value(
                        row,
                        "doctor_score",
                        "评分员打分",
                        "rater_score",
                        "clinician_score",
                        "医生评分",
                    )
                ),
                "ai_score": cls._to_float_or_none(
                    cls._first_value(row, "ai_score", "AI打分", "ai评分", "标准分")
                ),
                "ai_scoring_basis": cls._to_text(basis),
            }
            difference = cls._to_float_or_none(cls._first_value(row, "difference", "差异", "difference_value"))
            if difference is not None:
                normalized_row["difference"] = difference
            normalized.append(normalized_row)
        return normalized

    @classmethod
    def _parse_text_table(cls, content: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for raw_line in content.splitlines():
            line = raw_line.strip().strip("|").strip()
            if not line or "|" not in line:
                continue
            if set(line.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
                continue

            columns = [column.strip() for column in line.split("|", 5)]
            if len(columns) < 5 or not columns[0].isdigit():
                continue
            if columns[0] in {"项目编号", "编号"}:
                continue

            item_number = int(columns[0])
            if item_number < 1 or item_number > len(HAMD17_ITEMS):
                continue
            item_name = columns[1] or HAMD17_ITEMS[item_number - 1]
            if not re.match(r"^\s*\d{1,2}\s*[.、)]", item_name):
                item_name = f"{item_number}.{item_name}"
            rows.append(
                {
                    "hamd_item": item_name,
                    "doctor_score": cls._to_float_or_none(columns[2]),
                    "ai_score": cls._to_float_or_none(columns[3]),
                    "ai_scoring_basis": columns[4] or None,
                    "difference": cls._to_float_or_none(columns[5]) if len(columns) > 5 else None,
                }
            )
        return rows

    @staticmethod
    def _first_value(row: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in row:
                return row[key]
        return None

    @classmethod
    def _first_number(cls, row: dict[str, Any], *keys: str) -> float | None:
        for key in keys:
            value = cls._to_float_or_none(row.get(key))
            if value is not None:
                return value
        return None

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
