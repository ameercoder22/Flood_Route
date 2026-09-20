from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    aws_region: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""
    s3_bucket_name: str = ""
    dynamodb_table_name: str = "FloodReports"
    bedrock_model_id: str = ""
    nasa_api_key: str = ""
    nasa_earthdata_username: str = ""
    nasa_earthdata_password: str = ""
    max_upload_size_mb: float = Field(default=5.0, gt=0, le=20)
    allowed_image_types: str = "image/jpeg,image/png,image/webp"
    cors_origins: str = "http://localhost:5173"
    demo_mode: bool = False
    s3_presigned_url_expiry: int = Field(default=900, ge=60, le=3600)

    @property
    def allowed_content_types(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_image_types.split(",") if item.strip()}

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return int(self.max_upload_size_mb * 1024 * 1024)

    def require_aws(self, *names: str) -> None:
        missing: list[str] = []
        for name in names:
            value = getattr(self, name, "")
            if not value:
                missing.append(name.upper())
        if missing:
            raise RuntimeError("Missing required configuration: " + ", ".join(missing))


@lru_cache
def get_settings() -> Settings:
    return Settings()
