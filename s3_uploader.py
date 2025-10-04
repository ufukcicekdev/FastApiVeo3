import boto3
import os
import uuid
from typing import Optional
from config import settings
import logging

logger = logging.getLogger(__name__)

class S3VideoUploader:
    def __init__(self):
        """Initialize S3 client for DigitalOcean Spaces"""
        if not all([
            settings.aws_access_key_id,
            settings.aws_secret_access_key,
            settings.aws_storage_bucket_name,
            settings.aws_s3_endpoint_url
        ]):
            raise ValueError("AWS S3 credentials not properly configured")
        
        self.s3_client = boto3.client(
            's3',
            region_name=settings.aws_s3_region_name,
            endpoint_url=settings.aws_s3_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        
        self.bucket_name = settings.aws_storage_bucket_name
        
    def upload_video(self, local_file_path: str, filename: Optional[str] = None) -> str:
        """
        Upload video to S3/DigitalOcean Spaces and return public URL
        
        Args:
            local_file_path: Path to the local video file
            filename: Optional custom filename (if None, generates UUID)
            
        Returns:
            Public URL to the uploaded video
        """
        try:
            # Generate filename if not provided
            if not filename:
                filename = f"videos/{uuid.uuid4()}.mp4"
            else:
                filename = f"videos/{filename}"
            
            # Upload file to S3 with public-read ACL
            self.s3_client.upload_file(
                local_file_path,
                self.bucket_name,
                filename,
                ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': 'video/mp4'
                }
            )
            
            # Generate public URL
            public_url = f"{settings.aws_s3_endpoint_url}/{self.bucket_name}/{filename}"
            
            logger.info(f"Video uploaded successfully: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload video to S3: {str(e)}")
            raise Exception(f"S3 upload failed: {str(e)}")
    
    def delete_video(self, filename: str) -> bool:
        """
        Delete video from S3/DigitalOcean Spaces
        
        Args:
            filename: Name of the file to delete (without videos/ prefix)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = f"videos/{filename}"
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Video deleted successfully: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete video from S3: {str(e)}")
            return False

# Global uploader instance
s3_uploader = S3VideoUploader()