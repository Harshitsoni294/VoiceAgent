#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from routers.email_draft import generate_email_with_gemini

async def test_email():
    try:
        text = "Write email to john@company.com tell him he is selected for interview"
        result = await generate_email_with_gemini(text)
        print("Success!")
        print(f"Gmail URL: {result['gmail_url']}")
        print(f"To: {result['to']}")
        print(f"Subject: {result['subject']}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_email())
