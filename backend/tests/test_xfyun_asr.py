import base64
import hashlib
import hmac
from urllib.parse import quote_plus

from app.services.xfyun_asr import XfyunAsrService


class DummyConfig:
    app_id = "app-id"
    api_key = "access-key"
    api_secret = "access-secret"
    web_api = "https://office-api-ist-dx.iflyaisol.com"
    hotwords = None


def test_spark_signature_matches_hmac_sha1() -> None:
    service = XfyunAsrService(DummyConfig())
    params = {
        "appId": "app-id",
        "accessKeyId": "access-key",
        "dateTime": "2025-09-08T22:58:29+0800",
        "signatureRandom": "moI5WkopgjL1EL5Y",
        "fileSize": "397144",
        "fileName": "one-minute-audio.mp3",
        "durationCheckDisable": "true",
        "language": "autodialect",
        "pd": "medical",
        "audioMode": "fileStream",
    }
    base_string = "&".join(f"{key}={quote_plus(str(value))}" for key, value in sorted(params.items()))
    expected = base64.b64encode(
        hmac.new(
            DummyConfig.api_secret.encode("utf-8"),
            base_string.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("utf-8")

    assert service._spark_signature(params) == expected


def test_parse_result_text_handles_order_result_payload() -> None:
    result = {
        "code": "000000",
        "content": {
            "orderResult": {
                "lattice": [
                    {
                        "json_1best": '{"st":{"rt":[{"ws":[{"cw":[{"w":"hello"}]}]}]}}',
                    },
                    {
                        "json_1best": '{"st":{"rt":[{"ws":[{"cw":[{"w":" world"}]}]}]}}',
                    },
                ]
            }
        },
    }

    assert XfyunAsrService._parse_result_text(result) == "hello world"
