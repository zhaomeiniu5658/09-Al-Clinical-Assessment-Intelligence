import base64
import hashlib
import hmac
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings
from app.models.system import XfyunAsrSettings


class XfyunAsrService:
    """讯飞录音文件转写 LFASR 客户端。"""

    chunk_size = 10 * 1024 * 1024
    video_extensions = {".mp4"}

    def __init__(self, config: XfyunAsrSettings | None = None) -> None:
        self.app_id = config.app_id if config else settings.xfyun_app_id
        self.api_key = config.api_key if config else settings.xfyun_api_key
        self.api_secret = config.api_secret if config else settings.xfyun_api_secret
        self.base_url = (config.web_api if config else settings.xfyun_asr_base_url).rstrip("/")
        self.hotwords = config.hotwords if config else ""
        self.timeout_seconds = settings.xfyun_timeout_seconds

    def transcribe(self, audio_path: str, filename: str) -> str:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError("音频文件不存在")
        if not all([self.app_id, self.api_key, self.api_secret]):
            raise RuntimeError("未配置讯飞 ASR 认证信息")

        converted_path: Path | None = None
        source_path = path
        source_name = filename
        if path.suffix.lower() in self.video_extensions:
            converted_path = self._extract_audio(path)
            source_path = converted_path
            source_name = f"{Path(filename).stem}.wav"

        try:
            with httpx.Client(timeout=60) as client:
                order_id = self._prepare(client, source_path, source_name)
                self._upload(client, order_id, source_path)
                self._merge(client, order_id)
                return self._poll_result(client, order_id)
        finally:
            if converted_path:
                converted_path.unlink(missing_ok=True)

    @staticmethod
    def _extract_audio(video_path: Path) -> Path:
        descriptor, output_name = tempfile.mkstemp(prefix="asr-", suffix=".wav", dir=video_path.parent)
        os.close(descriptor)
        output_path = Path(output_name)
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(video_path),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-c:a",
                    "pcm_s16le",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            output_path.unlink(missing_ok=True)
            raise RuntimeError("服务器未安装 MP4 音轨提取组件") from exc

        if result.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
            output_path.unlink(missing_ok=True)
            detail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "无法读取视频音轨"
            raise RuntimeError(f"MP4 音轨提取失败: {detail}")
        return output_path

    def _prepare(self, client: httpx.Client, path: Path, filename: str) -> str:
        params = self._signed_params(
            {
                "file_len": str(path.stat().st_size),
                "file_name": filename,
                "duration": "0",
                "has_participle": "false",
            }
        )
        data = self._post_form(client, "/prepare", params)
        order_id = data.get("data")
        if not order_id:
            raise RuntimeError(f"讯飞 ASR prepare 未返回 orderId: {data}")
        return str(order_id)

    def _upload(self, client: httpx.Client, order_id: str, path: Path) -> None:
        with path.open("rb") as source:
            chunk_index = 0
            while chunk := source.read(self.chunk_size):
                params = self._signed_params(
                    {
                        "upload_id": order_id,
                        "slice_id": self._slice_id(chunk_index),
                    }
                )
                files = {"content": ("blob", chunk, "application/octet-stream")}
                self._post_form(client, "/upload", params, files=files)
                chunk_index += 1

    def _merge(self, client: httpx.Client, order_id: str) -> None:
        self._post_form(client, "/merge", self._signed_params({"upload_id": order_id}))

    def _poll_result(self, client: httpx.Client, order_id: str) -> str:
        deadline = time.time() + self.timeout_seconds
        while time.time() < deadline:
            progress = self._post_form(client, "/getProgress", self._signed_params({"orderId": order_id}))
            status = str((progress.get("data") or {}).get("status") or progress.get("status") or "")
            if status == "9":
                result = self._post_form(client, "/getResult", self._signed_params({"orderId": order_id}))
                return self._parse_result_text(result)
            if status in {"-1", "4"}:
                raise RuntimeError(f"讯飞 ASR 识别失败: {progress}")
            time.sleep(settings.xfyun_poll_interval_seconds)
        raise TimeoutError("讯飞 ASR 识别超时")

    def _post_form(
        self,
        client: httpx.Client,
        path: str,
        data: dict[str, Any],
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = client.post(f"{self.base_url}{path}", data=data, files=files)
        response.raise_for_status()
        payload = response.json()
        code = str(payload.get("code", payload.get("ok", "0")))
        if code not in {"0", "000000", "true"}:
            raise RuntimeError(f"讯飞 ASR 接口错误: {payload}")
        return payload

    def _signed_params(self, params: dict[str, Any]) -> dict[str, Any]:
        ts = str(int(time.time()))
        base = self.api_key + ts
        md5 = hashlib.md5(base.encode("utf-8")).hexdigest()
        signa = hmac.new(self.api_secret.encode("utf-8"), md5.encode("utf-8"), hashlib.sha1).digest()
        return {
            "app_id": self.app_id,
            "ts": ts,
            "signa": base64.b64encode(signa).decode("utf-8"),
            **params,
        }

    @staticmethod
    def _slice_id(index: int) -> str:
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        first = alphabet[(index // 26) % 26]
        second = alphabet[index % 26]
        return f"{first}{second}"

    @staticmethod
    def _parse_result_text(result: dict[str, Any]) -> str:
        data = result.get("data")
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError:
                return data
        else:
            parsed = data

        if isinstance(parsed, dict):
            lattice = parsed.get("lattice")
        else:
            lattice = parsed

        if isinstance(lattice, str):
            try:
                lattice = json.loads(lattice)
            except json.JSONDecodeError:
                return lattice

        pieces: list[str] = []
        if isinstance(lattice, list):
            for item in lattice:
                if not isinstance(item, dict):
                    continue
                json_1best = item.get("json_1best")
                if isinstance(json_1best, str):
                    try:
                        best = json.loads(json_1best)
                    except json.JSONDecodeError:
                        pieces.append(json_1best)
                        continue
                else:
                    best = json_1best
                pieces.extend(XfyunAsrService._words_from_best(best))

        text = "".join(pieces).strip()
        if not text:
            raise ValueError(f"无法解析讯飞 ASR 结果: {result}")
        return text

    @staticmethod
    def _words_from_best(best: Any) -> list[str]:
        words: list[str] = []
        if not isinstance(best, dict):
            return words
        for rt in best.get("st", {}).get("rt", []):
            for ws in rt.get("ws", []):
                for cw in ws.get("cw", []):
                    word = cw.get("w")
                    if word:
                        words.append(str(word))
        return words

