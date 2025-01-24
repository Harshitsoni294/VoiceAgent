from fastapi import APIRouter, Request
import httpx

router = APIRouter()

@router.post("")
async def search(request: Request):
    data = await request.json()
    question = data.get("question", "")
    # Use Hugging Face Inference API (no key, free model)
    url = "https://api-inference.huggingface.co/models/distilbert-base-uncased"
    payload = {"inputs": question}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        return {"error": "Model API error"}
