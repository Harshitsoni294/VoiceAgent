from fastapi import APIRouter, Request
import os
import httpx
import re
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
EMAIL_DIR = "email_drafts"
os.makedirs(EMAIL_DIR, exist_ok=True)

async def generate_email_with_gemini(text):
    """Generate email using Gemini API with specified prompt format"""
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if not gemini_api_key or gemini_api_key == "YOUR_GEMINI_API_KEY_HERE":
        # Fallback to simple parsing if no API key
        return parse_email_manually(text)
    
    # Create the exact prompt format you specified
    prompt = f"""You are an assistant that generates a single Gmail compose URL.

Instructions:
1. Extract the recipient email (to), subject, and body from the user query.
2. Improve the subject to make it concise, professional, and clear.
3. Improve the body for grammar, tone, and readability while keeping the original intent.
4. Return only the final URL in this exact format:
   https://mail.google.com/mail/?view=cm&fs=1&to={{to}}&su={{subject}}&body={{body}}
5. Encode:
   - Spaces as %20
   - Line breaks as %0A
6. Do not include anything other than the URL. No explanations, no extra text.

User query: {text}"""
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                generated_url = data['candidates'][0]['content']['parts'][0]['text'].strip()
                
                # Extract URL if there's extra text
                url_match = re.search(r'https://mail\.google\.com[^\s\n]+', generated_url)
                if url_match:
                    gmail_url = url_match.group(0)
                    
                    # Parse the URL to extract components for preview
                    parsed_url = urllib.parse.urlparse(gmail_url)
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    
                    return {
                        "gmail_url": gmail_url,
                        "to": urllib.parse.unquote(query_params.get('to', [''])[0]),
                        "subject": urllib.parse.unquote(query_params.get('su', [''])[0]),
                        "body": urllib.parse.unquote(query_params.get('body', [''])[0])
                    }
                else:
                    # If no URL found, fallback
                    return parse_email_manually(text)
            else:
                return parse_email_manually(text)
                
    except Exception as e:
        print(f"Gemini API error: {e}")
        return parse_email_manually(text)

def parse_email_manually(text):
    """Fallback manual email parsing"""
    # Extract recipient email
    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
    recipient = email_match.group(1) if email_match else "recipient@example.com"
    
    # Generate subject and body based on content
    text_lower = text.lower()
    
    if "interview" in text_lower and "selected" in text_lower:
        subject = "Interview Invitation"
        body = "Congratulations! You have been shortlisted for an interview. Please confirm your availability."
    elif "meeting" in text_lower:
        subject = "Meeting Request"
        body = "I would like to schedule a meeting with you. Please let me know your availability."
    elif "follow" in text_lower and "up" in text_lower:
        subject = "Follow-up"
        body = "I hope this email finds you well. I wanted to follow up on our previous conversation."
    elif "selected" in text_lower or "shortlisted" in text_lower:
        subject = "Selection Notification"
        body = "Congratulations! You have been selected. We will be in touch with next steps shortly."
    else:
        subject = "Important Message"
        body = "I hope this email finds you well. Thank you for your time."
    
    # Create Gmail URL manually
    to = urllib.parse.quote(recipient)
    su = urllib.parse.quote(subject)
    body_encoded = urllib.parse.quote(body.replace('\n', '%0A'))
    
    gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={to}&su={su}&body={body_encoded}"
    
    return {
        "gmail_url": gmail_url,
        "to": recipient,
        "subject": subject,
        "body": body
    }

@router.post("")
async def save_email(request: Request):
    data = await request.json()
    subject = data.get("subject", "No Subject")
    body = data.get("body", "")
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{subject.replace(' ', '_')}.txt"
    path = os.path.join(EMAIL_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Subject: {subject}\n\n{body}")
    return {"status": "saved", "filename": filename}

@router.post("/generate")
async def generate_email_draft(request: Request):
    """Generate email draft using Gemini API"""
    data = await request.json()
    text = data.get("text", "")
    
    # Generate email using Gemini API
    result = await generate_email_with_gemini(text)
    
    return {
        "gmail_url": result["gmail_url"],
        "preview": f"To: {result['to']}\nSubject: {result['subject']}"
    }
