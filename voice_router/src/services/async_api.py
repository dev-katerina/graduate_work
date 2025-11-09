import httpx
from core.config import settings

async def search_films(query_text: str):
    url = settings.async_api+"/v1/films/search"
    params = {
        "query": query_text,
        "page_number": 1,
        "page_size": 3,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data
