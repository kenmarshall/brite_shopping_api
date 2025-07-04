import os
import boto3
import requests
from urllib.parse import urlparse

class S3Uploader:
    """Simple utility to upload images to S3."""

    def __init__(self):
        self.bucket = os.getenv("S3_BUCKET_NAME")
        self.client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )

    def upload_image_from_url(self, image_url: str) -> str:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        filename = os.path.basename(urlparse(image_url).path)
        if not filename:
            filename = "image.jpg"
        self.client.put_object(
            Bucket=self.bucket,
            Key=filename,
            Body=response.content,
            ACL="public-read",
            ContentType=response.headers.get("Content-Type", "image/jpeg")
        )
        return f"https://{self.bucket}.s3.amazonaws.com/{filename}"

s3_uploader = S3Uploader()
