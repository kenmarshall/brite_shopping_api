import os
import boto3
import requests
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from app.services.logger_service import logger
from urllib.parse import urlparse
import mimetypes

class S3Uploader:
    """
    Handles downloading images from URLs and uploading them to an AWS S3 bucket.
    """
    def __init__(self, aws_access_key_id: str = None, aws_secret_access_key: str = None, region_name: str = None, bucket_name: str = None):
        self.aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = region_name or os.getenv("AWS_REGION")
        self.bucket_name = bucket_name or os.getenv("AWS_S3_BUCKET_NAME")
        self.logger = logger

        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.region_name, self.bucket_name]):
            self.logger.error("AWS credentials or S3 bucket configuration is missing. S3Uploader may not function.")
            # Depending on strictness, could raise ValueError here
            # For now, allow initialization but operations will fail.
            self.s3_client = None
            return

        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
            self.logger.info(f"S3Uploader initialized for bucket: {self.bucket_name} in region: {self.region_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None


    def _generate_s3_key(self, image_url: str, product_name: str = "unknown_product") -> str:
        """
        Generates a unique S3 key for the image.
        Example: products/unknown_product/image_filename.jpg
        """
        try:
            parsed_url = urlparse(image_url)
            image_filename = os.path.basename(parsed_url.path)
            if not image_filename: # if path is like /
                image_filename = "image.jpg" # default filename
        except Exception:
            image_filename = "image.jpg" # fallback

        # Sanitize product_name for use in S3 key path
        sane_product_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in product_name.lower().replace(" ", "_"))

        # To add more uniqueness, consider appending a timestamp or UUID
        # For now, product name and original filename should be reasonably unique for different products
        return f"products/{sane_product_name}/{image_filename}"

    def upload_image_from_url(self, image_url: str, product_name: str = "unknown_product") -> str | None:
        """
        Downloads an image from a URL and uploads it to S3.

        :param image_url: The URL of the image to download.
        :param product_name: The name of the product, used for organizing in S3.
        :return: The S3 URL of the uploaded image, or None if upload fails.
        """
        if not self.s3_client:
            self.logger.error("S3 client not initialized. Cannot upload image.")
            return None
        if not image_url:
            self.logger.warning("Image URL is empty, cannot upload.")
            return None

        try:
            self.logger.info(f"Attempting to download image from: {image_url}")
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type')
            file_extension = mimetypes.guess_extension(content_type) if content_type else '.jpg' # Default to .jpg
            if not file_extension: # If mimetypes can't guess, e.g. for 'image/webp' on some systems
                 if 'image/webp' in content_type: file_extension = '.webp'
                 elif 'image/jpeg' in content_type: file_extension = '.jpg'
                 elif 'image/png' in content_type: file_extension = '.png'
                 else: file_extension = '.jpg' # Fallback

            # Generate S3 key using original filename from URL + product name context
            # Ensure the key has the correct extension based on Content-Type
            s3_key_base = os.path.splitext(self._generate_s3_key(image_url, product_name))[0]
            s3_key = f"{s3_key_base}{file_extension}"


            self.logger.info(f"Uploading image to S3: {self.bucket_name}/{s3_key}")
            self.s3_client.upload_fileobj(
                response.raw,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ContentType': content_type or 'image/jpeg'} # Provide content type
            )

            # Construct the S3 URL (common format, adjust if using custom domain or different path style)
            s3_url = f"httpsโซุป://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{s3_key}"
            self.logger.info(f"Successfully uploaded image to S3: {s3_url}")
            return s3_url

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to download image from {image_url}: {e}")
            return None
        except (NoCredentialsError, PartialCredentialsError) as e:
            self.logger.error(f"AWS credentials error: {e}. Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set.")
            return None
        except ClientError as e:
            self.logger.error(f"AWS S3 client error: {e}. Check bucket permissions and region.")
            return None
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during image upload from {image_url}: {e}")
            return None

# Example Usage (requires AWS credentials and S3 bucket to be set in environment)
if __name__ == '__main__':
    # This will only work if you have AWS credentials and S3 bucket info set in your environment
    # and the S3 bucket has appropriate permissions.
    if not all(os.getenv(var) for var in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "AWS_S3_BUCKET_NAME"]):
        print("AWS environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_S3_BUCKET_NAME) not fully set. Skipping live S3Uploader test.")
    else:
        print("Testing S3Uploader with AWS S3...")
        uploader = S3Uploader()

        if not uploader.s3_client:
            print("S3 client could not be initialized. Check credentials and configuration.")
        else:
            # A publicly accessible image URL for testing
            test_image_url = "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
            test_product_name = "Google Test Product"

            print(f"\nAttempting to upload image: {test_image_url} for product: {test_product_name}")
            s3_image_url = uploader.upload_image_from_url(test_image_url, test_product_name)

            if s3_image_url:
                print(f"  Successfully uploaded. S3 URL: {s3_image_url}")
            else:
                print(f"  Failed to upload image.")

            # Test with a potentially problematic URL or one that might not be an image
            # test_image_url_invalid = "https://example.com/not_an_image.html"
            # print(f"\nAttempting to upload from potentially invalid URL: {test_image_url_invalid}")
            # s3_image_url_invalid = uploader.upload_image_from_url(test_image_url_invalid, "Invalid Test")
            # if s3_image_url_invalid:
            #     print(f"  Successfully uploaded (unexpected for non-image). S3 URL: {s3_image_url_invalid}")
            # else:
            #     print(f"  Failed to upload image (as expected for non-image or error).")

            # Test with an image URL that might not have an extension in the path
            test_image_url_no_ext = "https://images.unsplash.com/photo-1542990253-a781e04c0082?ixlib=rb-1.2.1&q=80&fm=jpg&crop=entropy&cs=tinysrgb&w=1080&fit=max"
            # Note: Unsplash URLs often have parameters that determine format. `fm=jpg` suggests JPEG.
            # The _generate_s3_key might create a key without an extension if relying solely on path.
            # The ContentType check should help assign the correct extension.
            print(f"\nAttempting to upload image with no clear extension in path: {test_image_url_no_ext}")
            s3_image_url_no_ext = uploader.upload_image_from_url(test_image_url_no_ext, "NoExt Test Product")
            if s3_image_url_no_ext:
                print(f"  Successfully uploaded. S3 URL: {s3_image_url_no_ext}")
            else:
                print(f"  Failed to upload image.")
