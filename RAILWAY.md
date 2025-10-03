# Railway Deployment Guide

## Required Environment Variables

Set these in Railway dashboard under Variables:

```
GOOGLE_API_KEY=your_actual_google_api_key_here
API_KEY=your_secure_api_key_32_chars_long
REQUIRE_AUTH=true
ENVIRONMENT=production
HOST=0.0.0.0
PORT=$PORT
LOG_LEVEL=INFO
MAX_VIDEO_DURATION=60
MAX_CONCURRENT_TASKS=5
```

## Generate API Key

**Method 1: Use the API endpoint (development):**
```bash
curl -X POST "http://localhost:8000/auth/generate-key"
```

**Method 2: Generate manually:**
```bash
# Generate a secure 32-character API key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Deployment Steps

### Method 1: GitHub Integration (Recommended)

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Railway deployment ready"
   git remote add origin https://github.com/yourusername/veo3api.git
   git push -u origin main
   ```

2. **Railway Dashboard:**
   - Go to railway.app
   - "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect Dockerfile
   - Set environment variables

### Method 2: Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway project new

# Set environment variables
railway variables set GOOGLE_API_KEY=your_api_key
railway variables set API_KEY=your_secure_api_key
railway variables set REQUIRE_AUTH=true
railway variables set ENVIRONMENT=production
railway variables set HOST=0.0.0.0
railway variables set PORT=$PORT
railway variables set LOG_LEVEL=INFO
railway variables set MAX_VIDEO_DURATION=60
railway variables set MAX_CONCURRENT_TASKS=5

# Deploy
railway up
```

## Post-Deployment Testing

```bash
# Replace with your Railway URL
RAILWAY_URL="https://your-project.up.railway.app"

# Health check
curl $RAILWAY_URL/health

# Test video generation (with authentication)
curl -X POST "$RAILWAY_URL/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "prompt": "A beautiful sunset",
    "duration": 5,
    "aspect_ratio": "9:16",
    "quality": "high"
  }'

# Verify authentication
curl -X GET "$RAILWAY_URL/auth/verify" \
  -H "Authorization: Bearer your_api_key"
```

## Important Notes

- Railway automatically provides $PORT environment variable
- Health check endpoint: `/health`
- Automatic HTTPS enabled
- Auto-scaling based on traffic
- Logs available in Railway dashboard