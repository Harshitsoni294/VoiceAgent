# Buddy Setup Guide

## Quick Start

### 1. Get Google Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

### 2. Configure Environment
1. Open `.env` file in the `server_buddy` folder
2. Replace `your_gemini_api_key_here` with your actual API key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

### 3. Start Buddy Server
**Option A: Using the batch file (Windows)**
- Double-click `start_buddy.bat`

**Option B: Manual start**
```bash
cd server_buddy
pip install -r requirements.txt
python main.py
```

### 4. Test Buddy
1. Open your browser and go to http://localhost:8001
2. You should see: `{"message": "Buddy server is running!", "version": "1.0.0"}`

### 5. Use in VoiceAgent
1. Make sure your main VoiceAgent frontend is running
2. In the chat interface, select "Buddy (Friendly Chat)" from the dropdown
3. Start chatting with Buddy!

## Troubleshooting

### "GOOGLE_API_KEY environment variable is required"
- Make sure you've added your API key to the `.env` file
- Restart the server after adding the key

### "Port 8001 is already in use"
- Change the PORT in `.env` file to a different number (e.g., 8002)
- Update `REACT_APP_BUDDY_API_URL` in the frontend `.env` file accordingly

### Dependencies installation fails
- Make sure you have Python 3.8 or higher installed
- Try updating pip: `python -m pip install --upgrade pip`
- Install dependencies manually: `pip install fastapi uvicorn langchain`

### Buddy doesn't remember conversations
- ChromaDB creates a local database automatically
- Make sure the server has write permissions in the folder
- Check if `chroma_db` folder is created in the server directory

## Features Verification

1. **Memory Test**: Ask Buddy to remember something, then reference it later
2. **Personality Test**: Chat casually and notice the friendly tone
3. **Context Test**: Have a longer conversation and see how Buddy references past messages

## Production Deployment

For production deployment:
1. Set up a proper PostgreSQL database
2. Update the `DATABASE_URL` in `.env`
3. Use a production WSGI server like Gunicorn
4. Set up proper environment variables on your hosting platform
