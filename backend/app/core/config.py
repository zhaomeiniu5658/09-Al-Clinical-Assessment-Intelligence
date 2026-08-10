from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Clinical Assessment QC"
    api_v1_prefix: str = "/api/v1"
    environment: str = "local"

    admin_username: str = "admin"
    admin_password: str = "ChangeMe123!"
    jwt_secret_key: str = "please-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12

    mysql_host: str = "mysql"
    mysql_port: int = 3306
    mysql_database: str = "clinical_qc"
    mysql_user: str = "clinical_qc"
    mysql_password: str = "clinical_qc_password"
    database_url: str | None = None

    redis_url: str = "redis://redis:6379/0"

    storage_dir: str = "storage"
    max_audio_size_mb: int = 100

    dify_openai_base_url: str = "https://api.dify.ai"
    dify_hamd_api_key: str = ""
    dify_hama_api_key: str = ""
    dify_phq9_api_key: str = ""
    dify_openai_model: str = "dify"
    dify_timeout_seconds: int = 120

    xfyun_app_id: str = ""
    xfyun_api_key: str = ""
    xfyun_api_secret: str = ""
    xfyun_asr_base_url: str = "https://raasr.xfyun.cn/v2/api"
    xfyun_poll_interval_seconds: int = 3
    xfyun_timeout_seconds: int = 900

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://localhost"])

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def storage_path(self) -> Path:
        return Path(self.storage_dir)

    @property
    def audio_storage_path(self) -> Path:
        return self.storage_path / "audio"

    @property
    def max_audio_size_bytes(self) -> int:
        return self.max_audio_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
