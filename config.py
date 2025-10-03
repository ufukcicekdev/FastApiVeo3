import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Video generation settings
    max_video_duration: int = int(os.getenv("MAX_VIDEO_DURATION", "60"))
    max_concurrent_tasks: int = int(os.getenv("MAX_CONCURRENT_TASKS", "10"))
    
    # API settings
    api_title: str = "Veo3 Video Generation API"
    api_description: str = "Generate videos from text prompts using Google Gemini Veo3"
    api_version: str = "1.0.0"

settings = Settings()