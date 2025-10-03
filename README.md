# Veo3 Video Generation API

A FastAPI-based service that generates videos from text prompts using Google Gemini Veo3 API. Perfect for integration with n8n workflows and other automation tools.

## Features

- 🎥 Generate videos from text prompts using Google Gemini Veo3
- 🚀 Fast and scalable FastAPI backend
- 📊 Task-based processing with status tracking
- 🐳 Docker support for easy deployment
- 🔗 n8n webhook endpoints for seamless integration
- 📝 Comprehensive API documentation
- ⚡ Asynchronous processing

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud API key with Gemini access
- Docker (optional)

### Installation

1. **Clone and setup environment:**
   ```bash
   cd /Users/mac/Desktop/veo3api
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the API:**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Build and run with Docker:**
   ```bash
   docker-compose up -d
   ```

2. **Check status:**
   ```bash
   docker-compose ps
   ```

## API Endpoints

### Core Endpoints

- `POST /generate` - Generate video from prompt
- `GET /status/{task_id}` - Check generation status
- `GET /tasks` - List all tasks
- `DELETE /tasks/{task_id}` - Cancel a task

### n8n Integration Endpoints

- `POST /webhook/generate` - Generate video (webhook-friendly)
- `GET /webhook/status/{task_id}` - Get status (webhook-friendly)

### Health & Documentation

- `GET /health` - Health check
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation

## Usage Examples

### Generate Video

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over the ocean with waves crashing",
    "duration": 10,
    "resolution": "1080p",
    "quality": "high",
    "aspect_ratio": "16:9"
  }'
```

**Mobile/TikTok Format (9:16):**
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A dancer performing in a studio",
    "duration": 15,
    "resolution": "1080p",
    "quality": "high",
    "aspect_ratio": "9:16",
    "fps": 30
  }'
```

**Instagram Square (1:1):**
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Food preparation in a kitchen",
    "duration": 8,
    "resolution": "1080p",
    "quality": "high",
    "aspect_ratio": "1:1"
  }'
```

**Cinematic Widescreen (21:9):**
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Epic car chase through city streets",
    "duration": 20,
    "resolution": "4k",
    "quality": "ultra",
    "aspect_ratio": "21:9",
    "style": "cinematic action movie"
  }'
```

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Video generation started",
  "created_at": "2024-01-01T12:00:00"
}
```

### Check Status

```bash
curl "http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000"
```

Response:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "video_url": "https://storage.googleapis.com/generated-videos/video.mp4",
  "created_at": "2024-01-01T12:00:00",
  "completed_at": "2024-01-01T12:01:30"
}
```

## n8n Integration

### Setup in n8n

1. **Add HTTP Request Node:**
   - Method: `POST`
   - URL: `http://your-api-host:8000/webhook/generate`
   - Headers: `Content-Type: application/json`

2. **Request Body:**
   ```json
   {
     "prompt": "{{ $json.prompt }}",
     "duration": 10,
     "resolution": "1080p",
     "quality": "high"
   }
   ```

3. **Add Status Check Node:**
   - Method: `GET`
   - URL: `http://your-api-host:8000/webhook/status/{{ $json.task_id }}`

### Sample n8n Workflow

```json
{
  "nodes": [
    {
      "name": "Generate Video",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://localhost:8000/webhook/generate",
        "options": {
          "bodyContentType": "json"
        },
        "bodyParametersJson": "{\n  \"prompt\": \"A cat playing with a ball\",\n  \"duration\": 5,\n  \"resolution\": \"720p\"\n}"
      }
    },
    {
      "name": "Check Status",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "=http://localhost:8000/webhook/status/{{ $json.task_id }}"
      }
    }
  ]
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Cloud API key (required) | - |
| `ENVIRONMENT` | Application environment | `development` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_VIDEO_DURATION` | Maximum video duration (seconds) | `60` |
| `MAX_CONCURRENT_TASKS` | Maximum concurrent generation tasks | `10` |

### Video Parameters

| Parameter | Type | Options | Default | Description |
|-----------|------|---------|---------|-------------|
| `prompt` | string | Any text description | Required | Video content description |
| `duration` | integer | 1-60 seconds | `5` | Video length |
| `resolution` | string | `720p`, `1080p`, `4k`, `540p` | `720p` | Video resolution |
| `quality` | string | `low`, `medium`, `high`, `ultra` | `medium` | Video quality |
| `aspect_ratio` | string | See aspect ratios below | `16:9` | Video dimensions |
| `format` | string | `mp4`, `webm`, `mov`, `avi` | `mp4` | Output format |
| `fps` | integer | 24-60 | `30` | Frames per second |
| `style` | string | Optional style description | `null` | Visual style |

### Supported Aspect Ratios

| Ratio | Format | Best For | Example Use Cases |
|-------|--------|----------|-------------------|
| `16:9` | Landscape | YouTube, TV, Desktop | Standard videos, tutorials, presentations |
| `9:16` | Portrait | Mobile, TikTok, Stories | Social media, mobile content, vertical videos |
| `1:1` | Square | Instagram, Social | Social media posts, profile videos |
| `21:9` | Cinematic | Movies, Trailers | Cinematic content, dramatic scenes |
| `4:3` | Classic | Retro, Traditional | Classic TV format, vintage style |
| `32:9` | Ultra-wide | Panoramic | Ultra-wide displays, panoramic content |

## Task Status

| Status | Description |
|--------|-------------|
| `processing` | Initial status, task queued |
| `analyzing_prompt` | Analyzing input prompt |
| `generating` | Video generation in progress |
| `finalizing` | Finalizing video output |
| `completed` | Video successfully generated |
| `failed` | Generation failed |
| `cancelled` | Task cancelled by user |

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (validation errors)
- `404` - Task not found
- `500` - Internal server error

Error response format:
```json
{
  "error": "ValidationError",
  "message": "Prompt is required",
  "details": "Additional error information"
}
```

## Development

### Running in Development Mode

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Test the API
curl http://localhost:8000/health
```

## Production Deployment

### Docker Compose (Recommended)

```bash
# Production deployment
docker-compose -f docker-compose.yml up -d

# With custom environment
ENV=production docker-compose up -d
```

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run with production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Security Considerations

- Always use HTTPS in production
- Secure your Google API key
- Implement rate limiting for public APIs
- Use proper authentication for sensitive deployments
- Monitor resource usage and set appropriate limits

## Troubleshooting

### Common Issues

1. **API Key Not Working:**
   - Verify your Google API key has Gemini access
   - Check the key is correctly set in `.env`

2. **Video Generation Fails:**
   - Check API quotas and limits
   - Verify prompt content follows Google's guidelines
   - Monitor logs for detailed error messages

3. **Performance Issues:**
   - Adjust `MAX_CONCURRENT_TASKS` based on your resources
   - Monitor memory usage during video generation
   - Consider scaling horizontally for high load

### Logs

```bash
# Docker logs
docker-compose logs -f veo3-api

# Local development
# Logs are printed to console
```

## Support

For issues and questions:
- Check the [API documentation](http://localhost:8000/docs)
- Review error messages in the logs
- Verify your Google API configuration

## License

This project is licensed under the MIT License.