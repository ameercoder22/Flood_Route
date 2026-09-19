from __future__ import annotations

import logging
import uuid
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


class StorageError(RuntimeError):
    pass


MAGIC = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF",),
}


class S3Service:
    def __init__(self, region: str, bucket_name: str, presigned_expiry: int = 900):
        if not region or not bucket_name:
            raise ValueError("AWS_REGION and S3_BUCKET_NAME are required for S3")
        self.bucket_name = bucket_name
        self.presigned_expiry = presigned_expiry
        self.client = boto3.client(
            "s3", region_name=region,
            config=Config(connect_timeout=10, read_timeout=30, retries={"max_attempts": 2, "mode": "standard"}),
        )

    @staticmethod
    def validate_image(content_type: str, filename: str, data: bytes, max_bytes: int, allowed_types: set[str]) -> str:
        normalized = (content_type or "").lower().strip()
        if normalized not in allowed_types:
            raise ValueError("Unsupported image type")
        if len(data) > max_bytes:
            raise ValueError("Image exceeds the maximum upload size")
        ext = Path(filename or "").suffix.lower()
        expected = {"image/jpeg": {".jpg", ".jpeg"}, "image/png": {".png"}, "image/webp": {".webp"}}
        if ext not in expected.get(normalized, set()):
            raise ValueError("Image extension does not match content type")
        signatures = MAGIC.get(normalized, ())
        if normalized == "image/webp":
            if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
                raise ValueError("Invalid WEBP image")
        elif not any(data.startswith(signature) for signature in signatures):
            raise ValueError("Invalid image content")
        return normalized

    def upload_image(self, report_id: str, filename: str, content_type: str, data: bytes) -> str:
        extension = Path(filename).suffix.lower().lstrip(".")
        key = f"reports/{report_id}/{uuid.uuid4().hex}.{extension}"
        try:
            self.client.put_object(Bucket=self.bucket_name, Key=key, Body=data, ContentType=content_type)
        except (ClientError, BotoCoreError, Exception) as exc:
            logger.exception("S3 upload failed for report %s", report_id)
            raise StorageError("Image upload failed") from exc
        return key

    def generate_presigned_url(self, key: str) -> str:
        try:
            return self.client.generate_presigned_url(
                "get_object", Params={"Bucket": self.bucket_name, "Key": key}, ExpiresIn=self.presigned_expiry
            )
        except (ClientError, BotoCoreError, Exception) as exc:
            logger.exception("Could not create presigned URL")
            raise StorageError("Could not create image access URL") from exc
