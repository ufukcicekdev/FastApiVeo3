# 🔐 API Authentication Guide

## Overview

The Veo3 Video Generation API uses Bearer Token authentication to secure endpoints. This prevents unauthorized access and usage of your video generation service.

## 🔑 How Authentication Works

1. **API Key Required**: All video generation endpoints require a valid API key
2. **Bearer Token**: Include the API key in the `Authorization` header
3. **Format**: `Authorization: Bearer your_api_key_here`

## 🚀 Getting Started

### Step 1: Generate API Key

**Development Mode:**
```bash
curl -X POST "http://localhost:8001/auth/generate-key"
```

**Manual Generation:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Response:**
```json
{
  "api_key": "s7v6hyDYGfkHAbQ7vlJE_v3IAbpYQlWviu8Oo1MFHeY",
  "message": "Save this key securely - it won't be shown again",
  "usage": "Add 'Authorization: Bearer <api_key>' header to requests"
}
```

### Step 2: Set Environment Variables

**For Railway Deployment:**
```bash
railway variables set API_KEY=your_generated_api_key
railway variables set REQUIRE_AUTH=true
```

**For Local Development (.env):**
```bash
API_KEY=your_generated_api_key
REQUIRE_AUTH=true
```

### Step 3: Use API Key in Requests

**Example Request:**
```bash
curl -X POST "https://your-app.up.railway.app/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key_here" \
  -d '{
    "prompt": "A beautiful sunset",
    "duration": 5,
    "aspect_ratio": "9:16"
  }'
```

## 🔧 Authentication Endpoints

### Verify Token
```bash
GET /auth/verify
Authorization: Bearer your_api_key
```

**Response:**
```json
{
  "valid": true,
  "message": "Token is valid",
  "token_preview": "s7v6hyDY..."
}
```

### Generate New Key (Development Only)
```bash
POST /auth/generate-key
```

## 🛡️ Protected Endpoints

All these endpoints require authentication:

- `POST /generate` - Generate video
- `GET /status/{task_id}` - Check video status
- `GET /tasks` - List all tasks
- `DELETE /tasks/{task_id}` - Cancel task
- `POST /webhook/generate` - n8n webhook
- `GET /webhook/status/{task_id}` - n8n status webhook

## 🌐 n8n Integration

### HTTP Request Node Configuration

1. **URL**: `https://your-app.up.railway.app/webhook/generate`
2. **Method**: `POST`
3. **Headers**:
   ```json
   {
     "Content-Type": "application/json",
     "Authorization": "Bearer your_api_key_here"
   }
   ```
4. **Body**:
   ```json
   {
     "prompt": "{{ $json.prompt }}",
     "duration": 10,
     "aspect_ratio": "9:16"
   }
   ```

### n8n Workflow Example

```json
{
  "nodes": [
    {
      "name": "Generate Video",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "https://your-app.up.railway.app/webhook/generate",
        "authentication": "headerAuth",
        "headerAuth": {
          "name": "Authorization",
          "value": "Bearer your_api_key_here"
        },
        "options": {
          "bodyContentType": "json"
        },
        "bodyParametersJson": "{\"prompt\": \"A cat playing\", \"duration\": 5}"
      }
    }
  ]
}
```

## 🔒 Security Features

### Development vs Production

- **Development**: API key generation endpoint available
- **Production**: Key generation disabled for security
- **Optional Auth**: Can disable auth in development with `REQUIRE_AUTH=false`

### Key Security

- **32-character keys**: Cryptographically secure
- **Bearer token format**: Industry standard
- **No key storage**: Keys not stored in logs
- **Preview only**: Token verification shows only first 8 characters

## ❌ Error Responses

### Missing Authorization Header
```json
{
  "detail": "Not authenticated"
}
```

### Invalid API Key
```json
{
  "detail": "Invalid API key"
}
```

### Production Key Generation Attempt
```json
{
  "detail": "API key generation not available in production"
}
```

## 🛠️ Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `""` | Your secure API key |
| `REQUIRE_AUTH` | `true` | Enable/disable authentication |
| `ENVIRONMENT` | `development` | Environment mode |

### Disable Authentication (Development Only)

```bash
REQUIRE_AUTH=false
```

This allows access without API key in development mode.

## 📝 Best Practices

1. **Store keys securely**: Use environment variables, never hardcode
2. **Rotate keys regularly**: Generate new keys periodically
3. **Monitor usage**: Check logs for unauthorized access attempts
4. **Use HTTPS**: Always use secure connections in production
5. **Limit access**: Only share keys with authorized users/services

## 🎯 Quick Test

```bash
# Health check (no auth required)
curl https://your-app.up.railway.app/health

# Test authentication
curl -H "Authorization: Bearer your_key" \
     https://your-app.up.railway.app/auth/verify

# Generate video
curl -X POST "https://your-app.up.railway.app/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_key" \
  -d '{"prompt": "test video", "duration": 5}'
```