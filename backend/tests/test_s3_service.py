import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from app.services.s3_service import S3Service, StorageError

# Constants
BUCKET_NAME = "test-bucket"
REGION = "us-east-1"
MAX_BYTES = 1024 * 5 # 5KB for testing

@pytest.fixture
def s3_service():
    return S3Service(REGION, BUCKET_NAME)

def test_validate_image_success(s3_service):
    data = b"\xff\xd8\xff" + b"somecontent" # JPEG signature
    s3_service.validate_image("image/jpeg", "test.jpg", data, MAX_BYTES, {"image/jpeg"})

def test_validate_image_invalid_type(s3_service):
    with pytest.raises(ValueError, match="Unsupported image type"):
        s3_service.validate_image("image/gif", "test.gif", b"data", MAX_BYTES, {"image/jpeg"})

def test_validate_image_too_large(s3_service):
    data = b"x" * (MAX_BYTES + 1)
    with pytest.raises(ValueError, match="Image exceeds the maximum upload size"):
        s3_service.validate_image("image/jpeg", "test.jpg", data, MAX_BYTES, {"image/jpeg"})

def test_validate_image_empty(s3_service):
    # Depending on implementation, empty might be validated by signature or size.
    # The current validation allows empty if size > 0 and signature match.
    # If data is empty bytes, signature check should fail if required.
    with pytest.raises(ValueError, match="Invalid image content"):
        s3_service.validate_image("image/jpeg", "test.jpg", b"", MAX_BYTES, {"image/jpeg"})

def test_upload_image_success(s3_service):
    s3_service.client = MagicMock()
    s3_service.upload_image("R001", "test.jpg", "image/jpeg", b"data")
    s3_service.client.put_object.assert_called_once()

def test_upload_image_failure(s3_service):
    s3_service.client = MagicMock()
    s3_service.client.put_object.side_effect = ClientError({"Error": {"Code": "500", "Message": "Internal Error"}}, "PutObject")
    with pytest.raises(StorageError, match="Image upload failed"):
        s3_service.upload_image("R001", "test.jpg", "image/jpeg", b"data")
