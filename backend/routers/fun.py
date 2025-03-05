from fastapi import APIRouter
import httpx

router = APIRouter()

@router.get("/joke")
async def get_joke():
    url = "https://official-joke-api.appspot.com/random_joke"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        return r.json()

@router.get("/quote")
async def get_quote():
    url = "https://type.fit/api/quotes"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        quotes = r.json()
        import random
        return random.choice(quotes)

@router.get("/fact")
async def get_fact():
    url = "https://uselessfacts.jsph.pl/random.json?language=en"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        return r.json()
