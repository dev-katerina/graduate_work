from fastapi import APIRouter, HTTPException, Depends
from elasticsearch import AsyncElasticsearch
from connections.elastic import get_elastic, RETRIABLE_EXCEPTIONS
from http import HTTPStatus
from services.auth import JWTBearer
import backoff
from api.v1.schemas import ApiMatch, ReadAPIMatch

router = APIRouter()

INDEX_NAME = "api_index"


@router.post("/", response_model=ReadAPIMatch)
@backoff.on_exception(
    backoff.expo,
    RETRIABLE_EXCEPTIONS,
    max_tries=5,
    jitter=backoff.full_jitter,
    on_backoff=lambda details: print(
        f"Backing off {details['wait']:0.1f}s after {details['tries']} tries "
        f"calling {details['target'].__name__}"
    )
)
async def create_item(item: ApiMatch, es: AsyncElasticsearch = Depends(get_elastic), 
    user: dict = Depends(JWTBearer())):
    """
    Создать документ.
    """
    result = await es.index(index=INDEX_NAME, document=item.dict())
    return ReadAPIMatch(id=result["_id"], **item.dict())


@router.get("/", response_model=list[ReadAPIMatch])
@backoff.on_exception(
    backoff.expo,
    RETRIABLE_EXCEPTIONS,
    max_tries=5,
    jitter=backoff.full_jitter,
    on_backoff=lambda details: print(
        f"Backing off {details['wait']:0.1f}s after {details['tries']} tries "
        f"calling {details['target'].__name__}"
    )
)
async def get_all(es: AsyncElasticsearch = Depends(get_elastic), 
    user: dict = Depends(JWTBearer())):
    """
    Получить все документы.
    """
    result = await es.search(
        index=INDEX_NAME,
        query={"match_all": {}},
        size=10000
    )

    return [
        ReadAPIMatch(id=hit["_id"], **hit["_source"])
        for hit in result["hits"]["hits"]
    ]


@router.get("/{id}", response_model=ReadAPIMatch)
@backoff.on_exception(
    backoff.expo,
    RETRIABLE_EXCEPTIONS,
    max_tries=5,
    jitter=backoff.full_jitter,
    on_backoff=lambda details: print(
        f"Backing off {details['wait']:0.1f}s after {details['tries']} tries "
        f"calling {details['target'].__name__}"
    )
)
async def get_item(id: str, es: AsyncElasticsearch = Depends(get_elastic), 
    user: dict = Depends(JWTBearer())):
    """
    Получить документ по ID.
    """
    try:
        result = await es.get(index=INDEX_NAME, id=id)
    except Exception:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Item not found")

    return ReadAPIMatch(id=result["_id"], **result["_source"])


@router.put("/{id}", response_model=ReadAPIMatch)
@backoff.on_exception(
    backoff.expo,
    RETRIABLE_EXCEPTIONS,
    max_tries=5,
    jitter=backoff.full_jitter,
    on_backoff=lambda details: print(
        f"Backing off {details['wait']:0.1f}s after {details['tries']} tries "
        f"calling {details['target'].__name__}"
    )
)
async def update_item(id: str, item: ApiMatch, es: AsyncElasticsearch = Depends(get_elastic), 
    user: dict = Depends(JWTBearer())):
    """
    Полностью обновить документ.
    """
    exists = await es.exists(index=INDEX_NAME, id=id)
    if not exists:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Item not found")

    await es.update(index=INDEX_NAME, id=id, doc=item.dict())

    return ReadAPIMatch(id=id, **item.dict())


@router.delete("/{id}", response_model=dict)
@backoff.on_exception(
    backoff.expo,
    RETRIABLE_EXCEPTIONS,
    max_tries=5,
    jitter=backoff.full_jitter,
    on_backoff=lambda details: print(
        f"Backing off {details['wait']:0.1f}s after {details['tries']} tries "
        f"calling {details['target'].__name__}"
    )
)
async def delete_item(id: str, es: AsyncElasticsearch = Depends(get_elastic), 
    user: dict = Depends(JWTBearer())):
    """
    Удалить документ по ID.
    """
    exists = await es.exists(index=INDEX_NAME, id=id)
    if not exists:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Item not found")

    result = await es.delete(index=INDEX_NAME, id=id)
    return {"id": id, "result": result["result"]}
