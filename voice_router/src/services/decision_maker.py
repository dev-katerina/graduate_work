from elasticsearch import AsyncElasticsearch
from functools import lru_cache
from fastapi import Depends
from connections.elastic import get_elastic
from typing import List, Dict
import asyncio
import json
from groq import Groq
from models.user_intention import ApiMatch, ApiParameter
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
            "query": {
                "match": {
                    "description": {
                        "query": text,
                        "fuzziness": "AUTO"
                    }
                }
            },
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

        if not hits:
            raise ValueError("Нет подходящего маршрута для данного текста")

        hit = hits[0]
        source = hit["_source"]

        # Корректное создание ApiMatch: параметры -> список ApiParameter
        parameters_raw = source.get("parameters", [])
        parameters = [ApiParameter(**p) for p in parameters_raw]

        return ApiMatch(
            api_uri=source["api_uri"],
            score=hit["_score"],
            voice_form=source.get("voice_form"),
            text_form=source.get("text_form"),
            parameters=parameters,
        )

    def format_parameters_for_prompt(self, params: list[ApiParameter]) -> list[dict]:
        result = []
        for p in params:
            result.append({
                "name": p.parameter_name,
                "default_value": p.default_value,
                "allowed_values": p.allowed_values
            })
        return result

    async def get_parameters(self, api_uri: ApiMatch, text: str) -> Dict[str, str]:
        # Извлекаем только имена параметров
        formatted_params = self.format_parameters_for_prompt(api_uri.parameters)
        prompt = f"""
        Извлеки и заполни параметры из текста.

        Текст: "{text}"
        Параметры (с ограничениями и значениями по умолчанию):
        {formatted_params}

        Верни результат в формате JSON.

        Пример:
        Параметры: ["genre", "page_size"]
        Текст: "Найди фильмы жанра комедия."
        Ответ:
        {{
            "genre": "комедия",
            "page_size": ""
        }}

        Правила:
        - Для каждого параметра, если значение не найдено в тексте, подставь default_value.
        - Если default_value пустой, подставь пустую строку.
        - Если allowed_values не пуст, выбирай значение только из них.
        - Верни ответ строго в формате JSON, начиная с фигурной скобки {{
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
