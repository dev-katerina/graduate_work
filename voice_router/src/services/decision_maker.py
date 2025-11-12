from elasticsearch import AsyncElasticsearch
from functools import lru_cache
from fastapi import Depends
from connections.elastic import get_elastic
from connections import intention_service
from transformers import pipeline
from typing import List, Dict
import re
import openai
import json

class DecisionMaker:
    def __init__(self, elastic: AsyncElasticsearch, ner_model):
        self.elastic = elastic
        self.ner_model = ner_model

    async def choose_uri(self, text: str):
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
            "explain": True,
            "highlight": {       # добавляем подсветку
                "fields": {
                    "description": {}
                }
            },
            "_source": ["api_uri", "description", "voice_form", "text_form", "parameters"]
        }

        result = await self.elastic.search(index="api_index", body=query)
        hits = result["hits"]["hits"]

           # Берём первый (наиболее релевантный)
        hit = hits[0]
        source = hit["_source"]
        highlight = hit.get("highlight", {})
        highlight_texts = highlight.get("description", [])

        return {
            "api_uri": source["api_uri"],
            "score": hit["_score"],
            "voice_form": source.get("voice_form"),
            "text_form": source.get("text_form"),
            "parameters": source.get("parameters"),
            "highlight": hit.get("highlight", {}),

        }

    async def choose_parameters(self, uri: str, text: str, parameters: List[str]):
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"api_uri": uri}},   # фильтр по URI, если нужен
                        {
                            "match": {
                                "key_words": {
                                    "query": text,
                                    "fuzziness": "AUTO"
                                }
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "key_words": {}
                }
            },
            "_source": ["api_uri", "default_value", "key_words", "parameter_name"]
        }
        result = await self.elastic.search(index="params_index", body=query)
        hits = result.get("hits", {}).get("hits", [])

        parameters_found = []

        for hit in hits:
            source = hit.get("_source", {})
            highlight = hit.get("highlight", {})
            highlight_texts = highlight.get("key_words", [])

            parameters_found.append({
                "api_uri": source.get("api_uri"),
                "parameter_name": source.get("parameter_name"),
                "default_value": source.get("default_value"),
                "score": hit.get("_score"),
                "highlight": highlight_texts
            })

        return parameters_found
    
    async def get_parameters(self, text: str, parameters: List[str]) -> Dict[str, str]:
        # Формируем промпт, чтобы модель вернула JSON с параметрами из текста
        prompt = f"""
        Определи значения следующих параметров из текста пользователя.
        Параметры: {parameters}

        Текст: "{text}"

        Верни ответ в формате JSON. Если параметр не найден — оставь его пустым.
        Пример:
        {{
          "query": "Звёздные войны",
          "page_number": "1",
          "page_size": "3"
        }}
        """

        response = await openai.ChatCompletion.acreate(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты — ассистент, который извлекает параметры из пользовательского текста."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
        )
        
        content = response['choices'][0]['message']['content']

        try:
            params = json.loads(content)
        except json.JSONDecodeError:
            # Если не смогли распарсить — возвращаем пустые параметры
            params = {param: "" for param in parameters}

        # На всякий случай — оставить только нужные параметры (отфильтровать лишнее)
        params_filtered = {param: params.get(param, "") for param in parameters}

        return params_filtered
        
         



@lru_cache()
def get_decision_maker(
    elastic: AsyncElasticsearch = Depends(get_elastic),
    ner_model = Depends(lambda: intention_service.ner_model)  # явно оборачиваем в Depends
) -> DecisionMaker:
    return DecisionMaker(elastic, ner_model)