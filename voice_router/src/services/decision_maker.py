from elasticsearch import AsyncElasticsearch
from functools import lru_cache
from fastapi import Depends
from connections.elastic import get_elastic
from typing import List, Dict
import asyncio
import json
from groq import Groq
from models.user_intention import ApiMatch
from core.config import settings


class DecisionMaker:
    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic
        api_key = settings.groq_api_key
        self.client = Groq(api_key=api_key)

    async def choose_uri(self, text: str) -> ApiMatch:
        """
        Находит наиболее релевантный api_uri на основе пользовательского текста.
        """
        query = {
            "query": {"match": {"description": {"query": text, "fuzziness": "AUTO"}}},
            "_source": [
                "api_uri",
                "description",
                "voice_form",
                "text_form",
                "parameters",
            ],
        }

        result = await self.elastic.search(index="api_index", body=query)
        hits = result["hits"]["hits"]

        # Берём первый (наиболее релевантный)
        hit = hits[0]
        source = hit["_source"]

        result = {
            "api_uri": source["api_uri"],
            "score": hit["_score"],
            "voice_form": source.get("voice_form"),
            "text_form": source.get("text_form"),
            "parameters": source.get("parameters"),
        }
        return ApiMatch(**result)


    async def get_parameters(self, api_uri: ApiMatch, text: str, parameters: List[str]) -> Dict[str, str]:
        prompt = f"""
        Извлеки и заполни параметры из текста.

        Текст: "{text}"
        Параметры: {api_uri.parameters}

        Верни результат в формате JSON.

        Пример:
        Параметры: ["genre", "page_size"]
        Текст: "Найди фильмы жанра комедия."
        Ответ:
        {{
            "genre": "комедия",
            "page_size": ""
        }}

        Начинай ответ с открывающей фигурной скобки {{
        """

        # Вызов Groq API через их SDK, обернут в asyncio.to_thread,
        # так как SDK, скорее всего, синхронный
        def sync_call():
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",  # или нужная тебе модель
            )
            return chat_completion.choices[0].message.content

        generated_text = await asyncio.to_thread(sync_call)

        try:
            json_start = generated_text.find("{")
            json_end = generated_text.rfind("}") + 1
            json_str = generated_text[json_start:json_end]
            result = json.loads(json_str)
            return result
        except Exception:
            return {}


@lru_cache()
def get_decision_maker(
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> DecisionMaker:
    return DecisionMaker(elastic)
