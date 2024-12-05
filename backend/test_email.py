#!/usr/bin/env python3
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_gemini():
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    print(f"API Key loaded: {gemini_api_key[:10] if gemini_api_key else 'None'}...")
    
    if not gemini_api_key:
        print("No Gemini API key found")
        return
    
    prompt = """Generate a professional email for: Write email to john@company.com tell him he is selected for interview
    
    Format:
    Subject: [subject here]
    Body: [body here]"""
    
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
            print("Making request to Gemini API...")
            response = await client.post(url, json=payload, headers=headers)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                generated_text = data['candidates'][0]['content']['parts'][0]['text']
                print(f"Generated text: {generated_text}")
                return True
            else:
                print(f"Error response: {response.text}")
                return False
                
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_gemini())
