import os
from dotenv import load_dotenv

# Load .env file only in development
if os.getenv("ENVIRONMENT", "development") == "development":
    load_dotenv()

class Settings:
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    host: str = os.getenv("HOST", "0.0.0.0")
    # Railway provides PORT environment variable
    port: int = int(os.getenv("PORT", "8000"))
    
    # Video generation settings
    max_video_duration: int = int(os.getenv("MAX_VIDEO_DURATION", "60"))
    max_concurrent_tasks: int = int(os.getenv("MAX_CONCURRENT_TASKS", "10"))
    
    # API settings
    api_title: str = "Veo3 Video Generation API"
    api_description: str = "Generate videos from text prompts using Google Gemini Veo3"
    api_version: str = "1.0.0"
    
    # Authentication settings
    api_key: str = os.getenv("API_KEY", "")
    require_auth: bool = os.getenv("REQUIRE_AUTH", "true").lower() == "true"
    
    # AWS S3 / DigitalOcean Spaces settings
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_storage_bucket_name: str = os.getenv("AWS_STORAGE_BUCKET_NAME", "")
    aws_s3_region_name: str = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
    aws_s3_endpoint_url: str = os.getenv("AWS_S3_ENDPOINT_URL", "")
    
    # Railway specific settings
    is_production: bool = environment == "production"
    debug: bool = environment == "development"

settings = Settings()