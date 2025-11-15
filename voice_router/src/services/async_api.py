import httpx
from core.config import settings
from models.user_intention import ApiMatch
from typing import List, Dict, Any

def convert_value(value: str, default: Any):
    """
    Конвертирует строковое значение из LLM к типу default_value.
    Если default_value = None → возвращает строку.
    """
    if value is None or value == "":
        return None

    # Если default отсутствует — оставляем строку
    if default is None:
        return value

    # Определяем тип по default_value
    if isinstance(default, int):
        try:
            return int(value)
        except ValueError:
            return default

    if isinstance(default, float):
        try:
            return float(value)
        except ValueError:
            return default

    # В других случаях — str
    return str(value)


async def search_films(api: ApiMatch, parameters: Dict[str, str]):
    """
    Делает запрос к API фильмов на основе найденного api_uri и извлечённых параметров.
    
    api.api_uri — строка, например "/api/v1/films/"
    parameters — dict с заполненными значениями, например {"genre": "фэнтези", "page_size": "10"}
    """

    url = settings.async_api + api.api_uri
    merged_params = {}

    for param in api.parameters:
        name = param.parameter_name
        default = param.default_value
        user_value = parameters.get(name)

        if user_value not in ("", None):
            merged_params[name] = convert_value(user_value, default)
        else:
            merged_params[name] = default

    clean_params = {
        k: v for k, v in merged_params.items()
        if v not in (None, "", [])
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=clean_params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print("API request failed:", e)
            return {"error": "API request failed", "details": str(e)}