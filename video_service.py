import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional
import google.generativeai as genai
from config import settings
from models import VideoGenerationRequest, VideoGenerationResponse, TaskStatusResponse
import logging
import tempfile
import os
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoGenerationService:
    def __init__(self):
        """Initialize the video generation service with Google Gemini API."""
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        genai.configure(api_key=settings.google_api_key)
        
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
            logger.info(f"Starting Veo3 API call with prompt: {prompt[:100]}...")
            
            # Prepare parameters for Veo3 API
            aspect_ratio_value = request.aspect_ratio.value if request.aspect_ratio and hasattr(request.aspect_ratio, 'value') else str(request.aspect_ratio) if request.aspect_ratio else "16:9"
            resolution_value = request.resolution.value if request.resolution and hasattr(request.resolution, 'value') else str(request.resolution) if request.resolution else "720p"
            
            # Build the payload - only include supported parameter combinations
            payload_instance = {
                "prompt": prompt,
                "personGeneration": "allow_all"
            }
            
            # Add aspectRatio - always supported
            payload_instance["aspectRatio"] = aspect_ratio_value
            
            # Add resolution only for supported combinations
            # According to docs: 720p (default), 1080p (16:9 only)
            if resolution_value == "1080p" and aspect_ratio_value == "16:9":
                payload_instance["resolution"] = "1080p"
            elif resolution_value == "720p":
                payload_instance["resolution"] = "720p"
            # For other combinations, don't include resolution (uses default)
            
            # Note: As of now, the google-generativeai library doesn't have direct Veo3 support
            # We need to use the REST API directly until the library is updated
            
            # Construct the API request
            api_url = "https://generativelanguage.googleapis.com/v1beta/models/veo-3.0-generate-001:predictLongRunning"
            headers = {
                "x-goog-api-key": settings.google_api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "instances": [payload_instance]
            }
            
            # Start the video generation operation
            logger.info(f"Sending request to Veo3 API with payload: {payload}")
            response = requests.post(api_url, headers=headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"API request failed with status {response.status_code}: {response.text}")
            
            operation_data = response.json()
            operation_name = operation_data.get("name")
            
            if not operation_name:
                raise Exception("No operation name returned from API")
            
            logger.info(f"Video generation operation started: {operation_name}")
            
            # Poll the operation status until the video is ready
            operation_url = f"https://generativelanguage.googleapis.com/v1beta/{operation_name}"
            
            while True:
                logger.info("Waiting for video generation to complete...")
                await asyncio.sleep(10)
                
                status_response = requests.get(operation_url, headers={"x-goog-api-key": settings.google_api_key})
                
                if status_response.status_code != 200:
                    raise Exception(f"Status check failed: {status_response.text}")
                
                status_data = status_response.json()
                
                if status_data.get("done"):
                    break
            
            logger.info("Video generation completed")
            
            # Extract video URI from response
            response_data = status_data.get("response", {})
            generate_response = response_data.get("generateVideoResponse", {})
            generated_samples = generate_response.get("generatedSamples", [])
            
            if not generated_samples:
                raise Exception("No generated video found in response")
            
            video_uri = generated_samples[0].get("video", {}).get("uri")
            
            if not video_uri:
                raise Exception("No video URI found in response")
            
            logger.info(f"Video available at: {video_uri}")
            
            # Return the video URI - this will be a Google Cloud Storage signed URL
            return {
                "video_url": video_uri,
                "duration": request.duration,
                "resolution": resolution_value,
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
    
    async def _download_video_from_uri(self, video_uri: str) -> str:
        """
        Download video from Google Cloud Storage URI to a temporary file.
        
        Args:
            video_uri: The video URI from Veo3 API
            
        Returns:
            Local path to the downloaded video file
        """
        try:
            headers = {"x-goog-api-key": settings.google_api_key}
            
            # Download the video file
            response = requests.get(video_uri, headers=headers, stream=True)
            response.raise_for_status()
            
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            video_filename = f"video_{uuid.uuid4()}.mp4"
            video_path = os.path.join(temp_dir, video_filename)
            
            # Save video to file
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Video downloaded to: {video_path}")
            return video_path
            
        except Exception as e:
            logger.error(f"Failed to download video: {str(e)}")
            raise

# Global service instance
video_service = VideoGenerationService()