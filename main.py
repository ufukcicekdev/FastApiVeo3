from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import logging

from models import (
    VideoGenerationRequest, 
    VideoGenerationResponse, 
    TaskStatusResponse, 
    ErrorResponse
)
from video_service import video_service
from config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Veo3 Video Generation API")
    yield
    logger.info("Shutting down Veo3 Video Generation API")

# Initialize FastAPI app
app = FastAPI(
    title="Veo3 Video Generation API",
    description="Generate videos from text prompts using Google Gemini Veo3",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint for health check."""
    return {
        "message": "Veo3 Video Generation API",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "veo3-video-api",
        "environment": settings.environment
    }

@app.post("/generate", response_model=VideoGenerationResponse, tags=["Video Generation"])
async def generate_video(request: VideoGenerationRequest):
    """
    Generate a video from a text prompt using Google Gemini Veo3.
    
    This endpoint accepts a text prompt and video parameters, then starts
    an asynchronous video generation process. Returns a task ID that can
    be used to check the generation status.
    
    - **prompt**: Text description of the video to generate (required)
    - **duration**: Video duration in seconds (1-60, default: 5)
    - **resolution**: Video resolution (720p, 1080p, 4k, 540p, default: 720p)
    - **quality**: Video quality (low, medium, high, ultra, default: medium)
    - **aspect_ratio**: Video aspect ratio options:
        - **16:9** - Standard landscape (default)
        - **9:16** - Portrait/vertical format (perfect for mobile, TikTok, Instagram Stories)
        - **1:1** - Square format (Instagram posts, social media)
        - **21:9** - Cinematic widescreen
        - **4:3** - Classic TV format
        - **32:9** - Ultra-wide format
    - **format**: Video output format (mp4, webm, mov, avi, default: mp4)
    - **fps**: Frames per second (24-60, default: 30)
    - **style**: Optional style/aesthetic for the video
    
    **Examples:**
    - Mobile/TikTok video: `{"aspect_ratio": "9:16", "resolution": "1080p"}`
    - Instagram square: `{"aspect_ratio": "1:1", "resolution": "1080p"}`
    - Cinematic: `{"aspect_ratio": "21:9", "resolution": "4k", "quality": "ultra"}`
    """
    try:
        logger.info(f"Received video generation request: {request.prompt[:100]}...")
        
        # Validate API key
        if not settings.google_api_key:
            raise HTTPException(
                status_code=500,
                detail="Google API key not configured"
            )
        
        # Generate video
        response = await video_service.generate_video(request)
        
        logger.info(f"Video generation started with task ID: {response.task_id}")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Video generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/status/{task_id}", response_model=TaskStatusResponse, tags=["Video Generation"])
async def get_task_status(task_id: str):
    """
    Get the status of a video generation task.
    
    Use this endpoint to check the progress and status of a video generation
    task using the task ID returned from the /generate endpoint.
    
    Possible statuses:
    - **processing**: Video generation is in progress
    - **analyzing_prompt**: Analyzing the input prompt
    - **generating**: Generating the video
    - **finalizing**: Finalizing the video
    - **completed**: Video generation completed successfully
    - **failed**: Video generation failed
    """
    try:
        task_status = video_service.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        return task_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/tasks", tags=["Video Generation"])
async def list_tasks():
    """
    List all video generation tasks.
    
    Returns a list of all video generation tasks with their current status.
    Useful for monitoring and debugging purposes.
    """
    try:
        tasks = video_service.list_tasks()
        return {
            "tasks": tasks,
            "total": len(tasks)
        }
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/tasks/{task_id}", tags=["Video Generation"])
async def cancel_task(task_id: str):
    """
    Cancel a video generation task.
    
    Cancels a running video generation task. Note that tasks that are already
    completed cannot be cancelled.
    """
    try:
        task_status = video_service.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        if task_status.status in ["completed", "failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel task with status: {task_status.status}"
            )
        
        # Update task status to cancelled
        if task_id in video_service.tasks:
            video_service.tasks[task_id]["status"] = "cancelled"
        
        return {"message": f"Task {task_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="ValidationError",
            message=str(exc)
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred"
        ).dict()
    )

# N8N webhook endpoint for easier integration
@app.post("/webhook/generate", response_model=VideoGenerationResponse, tags=["Webhooks"])
async def webhook_generate_video(request: VideoGenerationRequest):
    """
    Webhook endpoint for n8n integration.
    
    This is a dedicated endpoint for n8n workflows that provides the same
    functionality as /generate but with webhook-friendly response handling.
    """
    return await generate_video(request)

@app.get("/webhook/status/{task_id}", response_model=TaskStatusResponse, tags=["Webhooks"])
async def webhook_get_status(task_id: str):
    """
    Webhook endpoint to get task status for n8n integration.
    """
    return await get_task_status(task_id)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )