import io
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.config import settings

client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)


def ensure_bucket():
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)


def upload_file(object_key: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> str:
    ensure_bucket()
    client.put_object(
        settings.MINIO_BUCKET,
        object_key,
        io.BytesIO(file_bytes),
        len(file_bytes),
        content_type=content_type,
    )
    return object_key


def download_file(object_key: str) -> bytes:
    response = client.get_object(settings.MINIO_BUCKET, object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def get_presigned_url(object_key: str, expires: int = 3600) -> str:
    return client.presigned_get_object(
        settings.MINIO_BUCKET,
        object_key,
        expires=timedelta(seconds=expires),
    )


def delete_file(object_key: str):
    try:
        client.remove_object(settings.MINIO_BUCKET, object_key)
    except S3Error:
        pass
