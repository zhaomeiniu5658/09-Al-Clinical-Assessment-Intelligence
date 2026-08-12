import base64
import hashlib
import hmac
import json
import os
import secrets
import string
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote_plus

import httpx

from app.core.config import settings
from app.models.system import XfyunAsrSettings


class XfyunAsrService:
    """Xfyun ASR client for the recording-file transcription models."""

    chunk_size = 10 * 1024 * 1024

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
            raise FileNotFoundError("Audio file does not exist")
        if not all([self.app_id, self.api_key, self.api_secret]):
            raise RuntimeError("Xfyun ASR credentials are not configured")

        converted_path: Path | None = None
        source_path = path
        source_name = filename

        if self._uses_spark_asr_endpoint():
            converted_path = self._normalize_audio(path)
            source_path = converted_path
            source_name = f"{Path(filename).stem}.wav"

        try:
            with httpx.Client(timeout=60) as client:
                if self._uses_spark_asr_endpoint():
                    return self._transcribe_with_spark_asr(client, source_path, source_name)

                order_id = self._prepare(client, source_path, source_name)
                self._upload(client, order_id, source_path)
                self._merge(client, order_id)
                return self._poll_result(client, order_id)
        finally:
            if converted_path:
                converted_path.unlink(missing_ok=True)

    def _uses_spark_asr_endpoint(self) -> bool:
        legacy_markers = ("raasr.xfyun.cn", "/v2/api")
        normalized_url = self.base_url.lower()
        return not any(marker in normalized_url for marker in legacy_markers)

    @staticmethod
    def _normalize_audio(source_path: Path) -> Path:
        descriptor, output_name = tempfile.mkstemp(prefix="asr-", suffix=".wav", dir=source_path.parent)
        os.close(descriptor)
        output_path = Path(output_name)
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(source_path),
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
            raise RuntimeError("ffmpeg is required to normalize audio before Xfyun ASR upload") from exc

        if result.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
            output_path.unlink(missing_ok=True)
            detail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "unable to read audio"
            raise RuntimeError(f"Audio normalization failed: {detail}")
        return output_path

    def _transcribe_with_spark_asr(self, client: httpx.Client, path: Path, filename: str) -> str:
        signature_random = self._signature_random()
        upload_payload = self._spark_upload(client, path, filename, signature_random)
        content = upload_payload.get("content") or {}
        order_id = content.get("orderId")
        if not order_id:
            raise RuntimeError(f"Xfyun ASR upload did not return orderId: {upload_payload}")
        return self._spark_poll_result(client, str(order_id), signature_random)

    def _spark_upload(
        self,
        client: httpx.Client,
        path: Path,
        filename: str,
        signature_random: str,
    ) -> dict[str, Any]:
        params = {
            "appId": self.app_id,
            "accessKeyId": self.api_key,
            "dateTime": self._date_time(),
            "signatureRandom": signature_random,
            "fileSize": str(path.stat().st_size),
            "fileName": filename,
            "durationCheckDisable": "true",
            "language": "autodialect",
            "pd": "medical",
            "audioMode": "fileStream",
        }
        signature = self._spark_signature(params)
        headers = {
            "Content-Type": "application/octet-stream",
            "Content-Length": str(path.stat().st_size),
            "signature": signature,
        }
        response = client.post(
            f"{self.base_url}/v2/upload",
            params=params,
            headers=headers,
            content=self._iter_file(path),
        )
        return self._spark_json(response)

    def _spark_poll_result(self, client: httpx.Client, order_id: str, signature_random: str) -> str:
        deadline = time.time() + self.timeout_seconds
        while time.time() < deadline:
            params = {
                "accessKeyId": self.api_key,
                "dateTime": self._date_time(),
                "signatureRandom": signature_random,
                "orderId": order_id,
                "resultType": "transfer",
            }
            headers = {
                "Content-Type": "application/json",
                "signature": self._spark_signature(params),
            }
            result = self._spark_json(
                client.post(f"{self.base_url}/v2/getResult", params=params, headers=headers, json={})
            )
            content = result.get("content") or {}
            order_info = content.get("orderInfo") or {}
            status = str(order_info.get("status", ""))
            if status == "4":
                return self._parse_result_text(result)
            if status == "-1":
                raise RuntimeError(f"Xfyun ASR recognition failed: {result}")
            time.sleep(settings.xfyun_poll_interval_seconds)
        raise TimeoutError("Xfyun ASR recognition timed out")

    @staticmethod
    def _spark_json(response: httpx.Response) -> dict[str, Any]:
        response.raise_for_status()
        payload = response.json()
        if str(payload.get("code", "")) != "000000":
            raise RuntimeError(f"Xfyun ASR API error: {payload}")
        return payload

    def _spark_signature(self, params: dict[str, Any]) -> str:
        pairs: list[str] = []
        for key in sorted(params):
            if key == "signature":
                continue
            value = params[key]
            if value is None or value == "":
                continue
            pairs.append(f"{quote_plus(str(key))}={quote_plus(str(value))}")
        base_string = "&".join(pairs)
        digest = hmac.new(self.api_secret.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1).digest()
        return base64.b64encode(digest).decode("utf-8")

    @staticmethod
    def _date_time() -> str:
        return datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

    @staticmethod
    def _signature_random() -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(16))

    @staticmethod
    def _iter_file(path: Path) -> Iterable[bytes]:
        with path.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                yield chunk

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
            raise RuntimeError(f"Xfyun ASR prepare did not return orderId: {data}")
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
                raise RuntimeError(f"Xfyun ASR recognition failed: {progress}")
            time.sleep(settings.xfyun_poll_interval_seconds)
        raise TimeoutError("Xfyun ASR recognition timed out")

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
            raise RuntimeError(f"Xfyun ASR API error: {payload}")
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
        content = result.get("content")
        if isinstance(content, dict) and content.get("orderResult") is not None:
            data = content.get("orderResult")
        else:
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
            raise ValueError(f"Unable to parse Xfyun ASR result: {result}")
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
