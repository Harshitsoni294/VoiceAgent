from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Configuration
CLIENT_BASE_URL = os.getenv('CLIENT_BASE_URL', 'http://localhost:3000')

@router.post("")
async def open_app(request: Request):
    data = await request.json()
    command = data.get("command", "")
    # Simple mapping for demo
    app_urls = {
        "youtube": "https://www.youtube.com",
        "gmail": "https://mail.google.com",
        "google": "https://www.google.com",
        "todo": f"{CLIENT_BASE_URL}/todo",
        "to do": f"{CLIENT_BASE_URL}/todo",
        "calendar": f"{CLIENT_BASE_URL}/calendar"
    }
    for app, url in app_urls.items():
        if app in command.lower():
            return {"message": f"Opening {app}", "redirect_url": url, "speak": f"Opening {app}"}
    return JSONResponse({"error": "App not found"}, status_code=404)
