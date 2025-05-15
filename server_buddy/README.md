# Buddy - Your Friendly AI Assistant

Buddy is a conversational AI chatbot that remembers past conversations and talks like a good friend. It uses LangChain with RAG (Retrieval-Augmented Generation) to provide contextual responses based on conversation history.

## Features

- **Conversational Memory**: Remembers past conversations using ChromaDB vector storage
- **Friendly Personality**: Talks like a close friend with warm, casual language
- **Context-Aware**: Uses RAG to retrieve relevant past conversations
- **Google Gemini Integration**: Powered by Google's Gemini Pro model
- **Persistent Storage**: Local PostgreSQL-backed ChromaDB for conversation history

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
# Google Gemini API Key (Required)
GOOGLE_API_KEY=your_gemini_api_key_here

# Database Configuration (Optional - uses SQLite by default)
DATABASE_URL=postgresql://username:password@localhost:5432/buddy_db

# ChromaDB Configuration
CHROMA_DB_PATH=./chroma_db

# Server Configuration
HOST=0.0.0.0
PORT=8001
```

### 3. Get Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

### 4. Optional: PostgreSQL Setup

If you want to use PostgreSQL instead of SQLite:

```bash
# Install PostgreSQL (Windows)
# Download from: https://www.postgresql.org/download/windows/

# Create database
createdb buddy_db

# Update DATABASE_URL in .env
```

## Running the Server

```bash
python main.py
```

The server will start on `http://localhost:8001`

## API Endpoints

### POST /chat
Send a message to Buddy

**Request Body:**
```json
{
  "text": "Hello Buddy!"
}
```

**Response:**
```json
{
  "answer": "Hey there! Great to hear from you! How are you doing today?",
  "context_used": ["Previous conversation snippets..."]
}
```

### GET /health
Health check endpoint

### GET /
Root endpoint with server info

## How It Works

1. **User sends message** → Buddy receives the message
2. **Context retrieval** → Searches ChromaDB for relevant past conversations
3. **Memory integration** → Combines with recent conversation buffer
4. **Response generation** → Uses Gemini Pro to generate contextual response
5. **Storage** → Saves the new conversation for future reference

## Deployment

This server is designed to be deployed independently. You can:

1. Deploy on cloud platforms (Heroku, Railway, etc.)
2. Run locally alongside the main VoiceAgent
3. Use Docker for containerized deployment

## Directory Structure

```
server_buddy/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── .env                # Environment configuration
├── README.md           # This file
└── chroma_db/          # ChromaDB storage (created automatically)
```

## Integration with VoiceAgent

When integrated with the main VoiceAgent frontend:

1. User selects "Buddy" from bot selector
2. Frontend routes requests to `http://localhost:8001/chat`
3. Buddy processes with RAG pipeline
4. Response is returned and displayed in chat UI
