# VoiceAgent Backend

This is the FastAPI backend for the VoiceAgent AI voice assistant.

## Features
- Modular routers for each feature (open_app, search, reminders, email_draft, fun, weather_time)
- No paid APIs or API keys required
- Local JSON storage for reminders

## How to Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

The backend will be available at http://localhost:8000
