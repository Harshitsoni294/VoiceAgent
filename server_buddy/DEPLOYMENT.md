# Buddy Server Deployment on Render

## Quick Deploy Commands

### Build Command:
```bash
pip install -r requirements.txt
```

### Start Command:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Manual Deployment Steps

### 1. Create New Web Service on Render
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the `server_buddy` folder as the root directory

### 2. Service Configuration
- **Name**: `buddy-server` (or your preferred name)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Python Version**: `3.11.9` (specified in runtime.txt and .python-version)

### 3. Environment Variables
Add these environment variables in Render:

| Key | Value | Notes |
|-----|-------|-------|
| `GOOGLE_API_KEY` | `your-actual-api-key` | **Required** - Your Google Gemini API key |
| `CHROMA_DB_PATH` | `./chroma_db` | Optional - Database path |
| `HOST` | `0.0.0.0` | Optional - Server host |
| `PORT` | `$PORT` | Auto-set by Render |

### 4. Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy
3. Your service will be available at: `https://your-service-name.onrender.com`

## Testing Deployment

Once deployed, test these endpoints:
- **Health Check**: `GET https://your-service.onrender.com/health`
- **Root**: `GET https://your-service.onrender.com/`
- **Chat**: `POST https://your-service.onrender.com/chat`

## Frontend Integration

Update your frontend to use the deployed URL:
```javascript
// In your frontend code, replace localhost with your Render URL
const BUDDY_API_URL = 'https://your-buddy-server.onrender.com';
```

## Files Created for Deployment:
- `render.yaml` - Render service configuration
- `runtime.txt` - Python version specification
- `Procfile` - Alternative process file
- `requirements.txt` - Already exists with dependencies
- `.gitignore` - Excludes sensitive files

## Important Notes:
1. **Free Tier**: Render free tier may have cold starts (slower first request)
2. **Environment Variables**: Never commit API keys to Git
3. **Database**: ChromaDB will use disk storage (persistent across deployments)
4. **CORS**: Already configured for cross-origin requests
