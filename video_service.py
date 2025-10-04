import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional
import time
from google import genai
from google.genai import types
from config import settings
from models import VideoGenerationRequest, VideoGenerationResponse, TaskStatusResponse
import logging
import tempfile
import os
from s3_uploader import s3_uploader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoGenerationService:
    def __init__(self):
        """Initialize the video generation service with Google Gemini API."""
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        # Initialize the new Google GenAI client
        self.client = genai.Client(api_key=settings.google_api_key)
        
        # In-memory task storage (use Redis/database in production)
        self.tasks: Dict[str, Dict] = {}
        
    async def generate_video(self, request: VideoGenerationRequest) -> VideoGenerationResponse:
        """
        Generate a video from text prompt using Google Gemini Veo3 API.
        
        Args:
            request: Video generation request with prompt and parameters
            
        Returns:
            VideoGenerationResponse with task details
        """
        task_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # Store initial task
        self.tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "created_at": created_at,
            "request": request.dict(),
            "video_url": None,
            "error_message": None,
            "completed_at": None
        }
        
        # Start background video generation
        asyncio.create_task(self._process_video_generation(task_id, request))
        
        return VideoGenerationResponse(
            task_id=task_id,
            status="processing",
            message="Video generation started",
            created_at=created_at
        )
    
    async def _process_video_generation(self, task_id: str, request: VideoGenerationRequest):
        """
        Background task to process video generation.
        
        Args:
            task_id: Unique task identifier
            request: Video generation request
        """
        try:
            # Update progress
            self.tasks[task_id]["progress"] = 10
            self.tasks[task_id]["status"] = "analyzing_prompt"
            
            logger.info(f"Starting video generation for task {task_id}")
            
            # Prepare the enhanced prompt for Veo3
            enhanced_prompt = self._enhance_prompt(request)
            
            # Update progress
            self.tasks[task_id]["progress"] = 30
            self.tasks[task_id]["status"] = "generating"
            
            # Generate video using Gemini Veo3
            video_result = await self._call_veo3_api(enhanced_prompt, request)
            
            # Update progress
            self.tasks[task_id]["progress"] = 80
            self.tasks[task_id]["status"] = "finalizing"
            
            # Process the result
            if video_result and "video_url" in video_result:
                self.tasks[task_id].update({
                    "status": "completed",
                    "progress": 100,
                    "video_url": video_result["video_url"],
                    "thumbnail_url": video_result.get("thumbnail_url"),
                    "completed_at": datetime.now().isoformat()
                })
                logger.info(f"Video generation completed for task {task_id}")
            else:
                raise Exception("Failed to generate video - no result returned")
                
        except Exception as e:
            logger.error(f"Video generation failed for task {task_id}: {str(e)}")
            self.tasks[task_id].update({
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.now().isoformat()
            })
    
    def _enhance_prompt(self, request: VideoGenerationRequest) -> str:
        """
        Enhance the user prompt with technical specifications for Veo3.
        
        Args:
            request: Video generation request
            
        Returns:
            Enhanced prompt string
        """
        base_prompt = request.prompt
        
        # Determine video orientation based on aspect ratio
        orientation_hints = {
            "16:9": "landscape orientation, horizontal format, wide-screen",
            "9:16": "portrait orientation, vertical format, mobile-friendly", 
            "1:1": "square format, social media optimized",
            "21:9": "cinematic widescreen, ultra-wide format",
            "4:3": "classic format, traditional aspect ratio",
            "32:9": "ultra-wide panoramic format"
        }
        
        # Get aspect ratio value, handling both enum and string cases
        if request.aspect_ratio and hasattr(request.aspect_ratio, 'value'):
            aspect_ratio_value = request.aspect_ratio.value
        else:
            aspect_ratio_value = str(request.aspect_ratio) if request.aspect_ratio else "16:9"
            
        orientation_hint = orientation_hints.get(aspect_ratio_value, "standard format")
        
        # Add technical specifications
        enhanced = f"""Create a {request.duration}-second video with the following specifications:
        
Content: {base_prompt}

Technical Requirements:
- Resolution: {request.resolution.value if request.resolution else 'HD'}
- Quality: {request.quality.value if request.quality else 'medium'}
- Aspect Ratio: {aspect_ratio_value} ({orientation_hint})
- Duration: {request.duration} seconds
- Frame Rate: {getattr(request, 'fps', 30)} fps
- Format: {getattr(request.format, 'value', 'mp4') if hasattr(request, 'format') and request.format else 'mp4'}"""

        if request.style:
            enhanced += f"\n- Style: {request.style}"
            
        # Add format-specific optimization hints
        if aspect_ratio_value == "9:16":
            enhanced += "\n\nOptimization Notes: Optimize for vertical mobile viewing, ensure key elements are centered vertically, use larger text and clear visuals suitable for smartphone screens."
        elif aspect_ratio_value == "1:1":
            enhanced += "\n\nOptimization Notes: Optimize for square social media format, ensure content fits well within square boundaries, center important elements."
        elif aspect_ratio_value == "21:9":
            enhanced += "\n\nOptimization Notes: Create cinematic widescreen content, utilize the wide format for panoramic shots or dramatic compositions."
            
        enhanced += "\n\nGenerate a high-quality, professional video that matches the prompt description with smooth motion, proper lighting, and composition optimized for the specified aspect ratio."

        return enhanced
    
    async def _call_veo3_api(self, prompt: str, request: VideoGenerationRequest) -> Dict:
        """
        Call Google Gemini Veo3 API for video generation using the official SDK.
        
        Args:
            prompt: Enhanced prompt for video generation
            request: Original request parameters
            
        Returns:
            Dictionary containing video generation results
        """
        try:
            logger.info(f"Starting Veo3 API call with prompt: {prompt[:100]}...")
            
            # Prepare parameters for Veo3 API using SDK
            aspect_ratio_value = request.aspect_ratio.value if request.aspect_ratio and hasattr(request.aspect_ratio, 'value') else str(request.aspect_ratio) if request.aspect_ratio else "16:9"
            
            logger.info(f"Using SDK approach with aspect ratio: {aspect_ratio_value}")
            
            # Use the official SDK approach like in the documentation
            # For now, let's use the basic approach without config to avoid type issues
            operation = self.client.models.generate_videos(
                model="veo-3.0-fast-generate-001",
                prompt=prompt
            )
            
            logger.info(f"Video generation operation started: {operation.name if hasattr(operation, 'name') else 'unknown'}")
            
            # Poll the operation status until the video is ready (async version)
            max_attempts = 60  # 10 minutes max
            attempts = 0
            
            while not operation.done and attempts < max_attempts:
                logger.info(f"Waiting for video generation to complete... (attempt {attempts + 1}/{max_attempts})")
                await asyncio.sleep(10)
                try:
                    operation = self.client.operations.get(operation)
                except Exception as e:
                    logger.warning(f"Error checking operation status: {e}")
                attempts += 1
            
            if not operation.done:
                raise Exception("Video generation timed out after 10 minutes")
            
            logger.info("Video generation completed")
            
            # Check if response exists and has the expected structure
            if not hasattr(operation, 'response') or not operation.response:
                raise Exception("No response received from video generation")
            
            if not hasattr(operation.response, 'generated_videos') or not operation.response.generated_videos:
                raise Exception("No generated videos found in response")
            
            generated_video = operation.response.generated_videos[0]
            
            # Create a temporary directory for the video download
            temp_dir = tempfile.mkdtemp()
            video_filename = f"video_{uuid.uuid4()}.mp4"
            temp_video_path = os.path.join(temp_dir, video_filename)
            
            # Try to download the video file using SDK
            public_video_url = None
            try:
                if hasattr(generated_video, 'video') and generated_video.video:
                    self.client.files.download(file=generated_video.video)
                    if hasattr(generated_video.video, 'save'):
                        generated_video.video.save(temp_video_path)
                    else:
                        # Alternative: save raw bytes if available
                        video_bytes = getattr(generated_video.video, 'video_bytes', None)
                        if video_bytes:
                            with open(temp_video_path, 'wb') as f:
                                f.write(video_bytes)
                        else:
                            raise Exception("No video bytes available")
                    
                    # Upload to S3 and get public URL
                    public_video_url = s3_uploader.upload_video(temp_video_path, video_filename)
                    
                    # Clean up temporary file
                    os.remove(temp_video_path)
                    os.rmdir(temp_dir)
                    
                    logger.info(f"Video uploaded to S3: {public_video_url}")
                    
                else:
                    raise Exception("No video file found in generated video")
            except Exception as download_error:
                logger.error(f"Download/upload error: {download_error}")
                # Clean up temp files if they exist
                if os.path.exists(temp_video_path):
                    os.remove(temp_video_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
                raise Exception(f"Failed to process video: {download_error}")
            
            logger.info(f"Video processing completed: {public_video_url}")
            
            # Return the video information
            return {
                "video_url": public_video_url,  # S3 Public URL
                "duration": request.duration,
                "resolution": "auto",  # SDK auto-selects
                "aspect_ratio": aspect_ratio_value,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Veo3 API call failed: {str(e)}")
            raise Exception(f"Video generation API error: {str(e)}")
    

    
    def get_task_status(self, task_id: str) -> Optional[TaskStatusResponse]:
        """
        Get the status of a video generation task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            TaskStatusResponse or None if task not found
        """
        if task_id not in self.tasks:
            return None
            
        task = self.tasks[task_id]
        
        return TaskStatusResponse(
            task_id=task_id,
            status=task["status"],
            progress=task.get("progress"),
            video_url=task.get("video_url"),
            error_message=task.get("error_message"),
            created_at=task["created_at"],
            completed_at=task.get("completed_at")
        )
    
    def list_tasks(self) -> Dict[str, TaskStatusResponse]:
        """
        List all video generation tasks.
        
        Returns:
            Dictionary of task IDs to TaskStatusResponse
        """
        result = {}
        for task_id in self.tasks.keys():
            task_status = self.get_task_status(task_id)
            if task_status:
                result[task_id] = task_status
        return result
    


# Global service instance
video_service = VideoGenerationService()