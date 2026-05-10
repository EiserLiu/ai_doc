import io

from minio import Minio

from app.config import settings

client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)


def download_file(bucket: str, object_key: str) -> bytes:
    response = client.get_object(bucket, object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def upload_file(bucket: str, object_key: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> str:
    client.put_object(
        bucket,
        object_key,
        io.BytesIO(file_bytes),
        len(file_bytes),
        content_type=content_type,
    )
    return object_key
