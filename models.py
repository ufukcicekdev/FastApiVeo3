from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class VideoResolution(str, Enum):
    HD = "720p"
    FULL_HD = "1080p"
    UHD = "4k"
    MOBILE_HD = "540p"  # For mobile/vertical content

class VideoQuality(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"

class AspectRatio(str, Enum):
    LANDSCAPE = "16:9"      # Standard landscape
    PORTRAIT = "9:16"       # Vertical/Mobile format
    SQUARE = "1:1"          # Square format
    WIDESCREEN = "21:9"     # Cinematic widescreen
    CLASSIC = "4:3"         # Classic TV format
    ULTRAWIDE = "32:9"      # Ultra-wide format

class VideoFormat(str, Enum):
    MP4 = "mp4"
    WEBM = "webm"
    MOV = "mov"
    AVI = "avi"

class VideoGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt to generate video from", min_length=1, max_length=2000)
    duration: Optional[int] = Field(default=5, description="Video duration in seconds", ge=1, le=60)
    resolution: Optional[VideoResolution] = Field(default=VideoResolution.HD, description="Video resolution")
    quality: Optional[VideoQuality] = Field(default=VideoQuality.MEDIUM, description="Video quality")
    aspect_ratio: Optional[AspectRatio] = Field(default=AspectRatio.LANDSCAPE, description="Video aspect ratio")
    format: Optional[VideoFormat] = Field(default=VideoFormat.MP4, description="Video output format")
    fps: Optional[int] = Field(default=30, description="Frames per second", ge=24, le=60)
    style: Optional[str] = Field(default=None, description="Video style/aesthetic")

class VideoGenerationResponse(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Generation status")
    message: str = Field(..., description="Status message")
    video_url: Optional[str] = Field(default=None, description="Generated video URL")
    thumbnail_url: Optional[str] = Field(default=None, description="Video thumbnail URL")
    duration: Optional[int] = Field(default=None, description="Actual video duration")
    created_at: str = Field(..., description="Creation timestamp")

class TaskStatusResponse(BaseModel):
    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Current status")
    progress: Optional[int] = Field(default=None, description="Progress percentage")
    video_url: Optional[str] = Field(default=None, description="Generated video URL if completed")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    created_at: str = Field(..., description="Creation timestamp")
    completed_at: Optional[str] = Field(default=None, description="Completion timestamp")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(default=None, description="Additional error details")