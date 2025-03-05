from fastapi import APIRouter, Request
import httpx
import os
import re
import urllib.parse
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# List of possible intents and their labels
INTENT_LABELS = [
    "weather_time",
    "fun_joke", 
    "fun_quote",
    "fun_fact",
    "open_app",
    "reminders",
    "email_draft",
    "search"
]

BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000/mcp')

# Helper functions
def parse_date(text):
    """Convert relative dates to actual dates"""
    today = datetime.now().date()
    text_lower = text.lower()
    
    if "today" in text_lower:
        return today.strftime("%Y-%m-%d")
    elif "tomorrow" in text_lower:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    elif "day after tomorrow" in text_lower:
        return (today + timedelta(days=2)).strftime("%Y-%m-%d")
    elif "tonight" in text_lower:
        return today.strftime("%Y-%m-%d")
    
    # Try to extract date patterns like "7 September 2025" or "September 7"
    date_match = re.search(r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)(\s+\d{4})?', text_lower)
    if date_match:
        day = date_match.group(1)
        month = date_match.group(2)
        year = date_match.group(3).strip() if date_match.group(3) else str(today.year)
        month_num = ["january","february","march","april","may","june","july","august","september","october","november","december"].index(month) + 1
        return f"{year}-{month_num:02d}-{int(day):02d}"
    
    return today.strftime("%Y-%m-%d")

def parse_time(text):
    """Extract time from text"""
    time_match = re.search(r'(\d{1,2}):?(\d{0,2})\s*(am|pm|a\.m\.|p\.m\.)?', text.lower())
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        period = time_match.group(3)
        
        if period and 'p' in period.lower() and hour != 12:
            hour += 12
        elif period and 'a' in period.lower() and hour == 12:
            hour = 0
            
        return f"{hour:02d}:{minute:02d}"
    return "09:00"  # Default time

def parse_reminder_request(text):
    """Parse reminder/meeting request"""
    date = parse_date(text)
    time = parse_time(text)
    
    # Extract the main content more intelligently
    original_text = text.lower()
    
    # Check if it's a general meeting/appointment request
    if any(word in original_text for word in ["meeting", "appointment", "call"]):
        if "meeting" in original_text:
            reminder_text = "Meeting"
        elif "appointment" in original_text:
            reminder_text = "Appointment" 
        elif "call" in original_text:
            reminder_text = "Call"
        else:
            reminder_text = "Meeting"
    else:
        # For other reminders, try to extract meaningful content
        # Remove scheduling words and time/date references more comprehensively
        reminder_text = re.sub(r'(schedule|set\s+a?\s*reminder|remind\s+me(\s+to|\s+for)?|at\s+\d{1,2}:?\d{0,2}\s*[ap]\.?m\.?|today|tomorrow|day\s+after\s+tomorrow)', '', text, flags=re.IGNORECASE)
        # Clean up extra whitespace
        reminder_text = re.sub(r'\s+', ' ', reminder_text).strip()
        
        # If the result starts with common words, extract the main subject
        if reminder_text:
            # Capitalize first letter for better display
            reminder_text = reminder_text.capitalize()
        
        # If still empty or too short, provide default
        if not reminder_text or len(reminder_text.strip()) < 3:
            reminder_text = "Reminder"
    
    return {
        "text": reminder_text,
        "date": date,
        "time": time
    }

def create_gmail_link(email_content):
    """Create Gmail compose link"""
    subject = urllib.parse.quote(email_content["subject"])
    body = urllib.parse.quote(email_content["body"])
    return f"https://mail.google.com/mail/?view=cm&fs=1&su={subject}&body={body}"

# Fallback intent detection for when HF API fails
def fallback_intent_detection(text):
    text_lower = text.lower()
    # Check for negative commands first
    if any(neg in text_lower for neg in ["don't", "do not", "dont", "never", "stop"]):
        return "search"
    # Simple keyword matching as fallback
    if any(word in text_lower for word in ["weather", "temperature", "rain", "forecast", "time", "clock", "what time"]):
        return "weather_time"
    if "joke" in text_lower or "funny" in text_lower:
        return "fun_joke"
    if "quote" in text_lower:
        return "fun_quote"
    if "fact" in text_lower:
        return "fun_fact"
    if any(word in text_lower for word in ["open", "start", "launch", "play"]):
        return "open_app"
    # Update fallback intent detection to include 'alarm' in reminders intent
    if any(word in text_lower for word in ["remind", "reminder", "meeting", "appointment", "alarm"]):
        return "reminders"
    if any(word in text_lower for word in ["email", "mail", "draft"]):
        return "email_draft"
    return "search"

@router.post("")
async def intent_handler(request: Request):
    data = await request.json()
    text = data.get("text", "")

    # Get HF token from environment
    hf_token = os.getenv("HF_TOKEN")
    intent = "search"  # Default fallback
    
    # Try Hugging Face API first if token is available
    if hf_token and hf_token != "YOUR_TOKEN_HERE":
        try:
            hf_url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
            headers = {"Authorization": f"Bearer {hf_token}"}
            payload = {"sequence": text, "labels": INTENT_LABELS}
            
            async with httpx.AsyncClient() as client:
                hf_resp = await client.post(hf_url, json=payload, headers=headers)
                if hf_resp.status_code == 200:
                    hf_data = hf_resp.json()
                    if "labels" in hf_data and "scores" in hf_data and hf_data["labels"]:
                        intent = hf_data["labels"][0]
                    else:
                        intent = fallback_intent_detection(text)
                else:
                    intent = fallback_intent_detection(text)
        except Exception:
            intent = fallback_intent_detection(text)
    else:
        # Use fallback if no token provided
        intent = fallback_intent_detection(text)

    # Route to the correct MCP based on detected intent
    async with httpx.AsyncClient() as client:
        if intent == "weather_time":
            text_lower = text.lower()
            
            # Check if user is asking specifically for time
            if any(word in text_lower for word in ["time", "clock", "what time"]) and not any(word in text_lower for word in ["weather", "temperature", "rain", "forecast"]):
                r = await client.get(f"{BASE_URL}/weather_time/time")
                d = r.json()
                return {"answer": f"Current time: {d.get('formatted_time')} on {d.get('date')}"}
            
            # Check if user is asking specifically for weather
            elif any(word in text_lower for word in ["weather", "temperature", "rain", "forecast"]) and not any(word in text_lower for word in ["time", "clock"]):
                r = await client.get(f"{BASE_URL}/weather_time/weather")
                d = r.json()
                return {"answer": f"Current weather: {d.get('weather')}"}
            
            # Both or general request
            else:
                r = await client.get(f"{BASE_URL}/weather_time")
                d = r.json()
                return {"answer": f"Weather: {d.get('weather')}\nTime: {d.get('time')}"}
        if intent == "fun_joke":
            r = await client.get(f"{BASE_URL}/fun/joke")
            d = r.json()
            return {"answer": f"{d.get('setup', '')} {d.get('punchline', '')}"}
        if intent == "fun_quote":
            r = await client.get(f"{BASE_URL}/fun/quote")
            d = r.json()
            return {"answer": f"{d.get('text', '')} — {d.get('author', 'Unknown')}"}
        if intent == "fun_fact":
            r = await client.get(f"{BASE_URL}/fun/fact")
            d = r.json()
            return {"answer": d.get('text') or d.get('fact') or str(d)}
        if intent == "open_app":
            # Only open if not a negative command
            if any(neg in text.lower() for neg in ["don't open", "do not open", "dont open", "no open", "never open"]):
                return {"answer": "Not opening as per your request."}
            r = await client.post(f"{BASE_URL}/open_app", json={"command": text})
            d = r.json()
            if d.get("redirect_url"):
                return {"answer": f"Opening: {d['redirect_url']}", "redirect_url": d["redirect_url"]}
            return {"answer": d.get("error") or str(d)}
        if intent == "reminders":
            # Parse reminder/meeting/alarm request and add to reminders
            reminder_data = parse_reminder_request(text)
            # No longer save to backend, just return the parsed data for frontend to save locally
            return {
                "answer": f"Reminder/Alarm added: {reminder_data['text']} on {reminder_data['date']} at {reminder_data['time']}", 
                "type": "reminder",
                "reminder_data": {
                    "text": reminder_data['text'],
                    "datetime": f"{reminder_data['date']} {reminder_data['time']}"
                }
            }
        if intent == "email_draft":
            # Generate email using Gemini API via email_draft router
            r = await client.post(f"{BASE_URL}/email_draft/generate", json={"text": text})
            d = r.json()
            if d.get("gmail_url"):
                return {"answer": f"Email generated: {d['preview']}", "redirect_url": d["gmail_url"]}
            return {"answer": d.get("preview", "Email generated successfully")}
        # Default: search
        r = await client.post(f"{BASE_URL}/search", json={"question": text})
        d = r.json()
        return {"answer": d.get('answer') or d[0].get('answer') if isinstance(d, list) and d else str(d)}

@router.post("/intent")
async def handle_intent(request: Request):
    data = await request.json()
    intent = data.get("intent")

    if intent == "open_todo":
        return {"action": "open", "app": "todo"}
    elif intent == "open_calendar":
        return {"action": "open", "app": "calendar"}

    return {"action": "unknown"}
