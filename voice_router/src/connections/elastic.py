from typing import Optional
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import ConnectionError, TransportError, NotFoundError

RETRIABLE_EXCEPTIONS = (ConnectionError, TransportError, NotFoundError)
es: Optional[AsyncElasticsearch] = None


# Функция понадобится при внедрении зависимостей
async def get_elastic() -> AsyncElasticsearch:
    return es
