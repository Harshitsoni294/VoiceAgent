from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(title="Test Email API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/test/email")
async def test_email_endpoint(request: Request):
    try:
        data = await request.json()
        text = data.get("text", "")
        
        # Simple response without Gemini API call
        return {
            "email_data": {
                "to": "john@company.com",
                "subject": "Interview Invitation", 
                "body": "Dear John, You have been selected for an interview."
            },
            "gmail_url": "https://mail.google.com/mail/?view=cm&fs=1&to=john@company.com&su=Interview%20Invitation&body=Dear%20John,%20You%20have%20been%20selected%20for%20an%20interview.",
            "preview": "To: john@company.com\nSubject: Interview Invitation"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
