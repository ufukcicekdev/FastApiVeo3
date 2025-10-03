import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional
import google.generativeai as genai
from config import settings
from models import VideoGenerationRequest, VideoGenerationResponse, TaskStatusResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoGenerationService:
    def __init__(self):
        """Initialize the video generation service with Google Gemini API."""
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro-exp-0827')
        
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
        Call Google Gemini Veo3 API for video generation.
        
        Args:
            prompt: Enhanced prompt for video generation
            request: Original request parameters
            
        Returns:
            Dictionary containing video generation results
        """
        try:
            # Note: This is a placeholder for the actual Veo3 API call
            # The actual Veo3 API endpoint may differ when officially released
            
            # Simulate API call delay
            await asyncio.sleep(5)  # Simulate processing time
            
            # For now, we'll use the text generation API and return a mock response
            # This should be replaced with actual Veo3 video generation API when available
            response = await self._mock_video_generation(prompt, request)
            
            return response
            
        except Exception as e:
            logger.error(f"Veo3 API call failed: {str(e)}")
            raise Exception(f"Video generation API error: {str(e)}")
    
    async def _mock_video_generation(self, prompt: str, request: VideoGenerationRequest) -> Dict:
        """
        Mock video generation for testing purposes.
        Replace this with actual Veo3 API call when available.
        
        Args:
            prompt: Video generation prompt
            request: Request parameters
            
        Returns:
            Mock video generation result
        """
        # This is a mock response - replace with actual Veo3 API integration
        mock_video_id = str(uuid.uuid4())
        
        return {
            "video_url": f"https://storage.googleapis.com/generated-videos/{mock_video_id}.mp4",
            "thumbnail_url": f"https://storage.googleapis.com/generated-videos/{mock_video_id}_thumb.jpg",
            "duration": request.duration,
            "resolution": request.resolution.value if request.resolution else 'HD',
            "status": "completed"
        }
    
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