import asyncio

import boto3
from botocore.config import Config

from app.core.config import settings

s3_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url or None,
    region_name=settings.s3_region,
    aws_access_key_id=settings.s3_access_key_id,
    aws_secret_access_key=settings.s3_secret_access_key.get_secret_value(),
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)


def presign_upload(key: str, content_type: str, expires_in: int) -> str:
    return s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.s3_bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )


def presign_download(key: str, expires_in: int) -> str:
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expires_in,
    )


async def delete_object(key: str) -> None:
    await asyncio.to_thread(s3_client.delete_object, Bucket=settings.s3_bucket, Key=key)


async def check_bucket() -> None:
    await asyncio.to_thread(s3_client.head_bucket, Bucket=settings.s3_bucket)
