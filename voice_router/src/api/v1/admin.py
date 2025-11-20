from fastapi import APIRouter, HTTPException, Depends
from elasticsearch import AsyncElasticsearch
from connections.elastic import get_elastic

from api.v1.schemas import ApiMatch, ReadAPIMatch

router = APIRouter(prefix="/api-index", tags=["API Index CRUD"])

INDEX_NAME = "api_index"


# --------------------
# CREATE
# --------------------
@router.post("/", response_model=ReadAPIMatch)
async def create_item(item: ApiMatch, es: AsyncElasticsearch = Depends(get_elastic)):
    """
    Создать документ.
    """
    result = await es.index(index=INDEX_NAME, document=item.dict())
    return ReadAPIMatch(id=result["_id"], **item.dict())


# --------------------
# READ ALL
# --------------------
@router.get("/", response_model=list[ReadAPIMatch])
async def get_all(es: AsyncElasticsearch = Depends(get_elastic)):
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


# --------------------
# READ ONE
# --------------------
@router.get("/{id}", response_model=ReadAPIMatch)
async def get_item(id: str, es: AsyncElasticsearch = Depends(get_elastic)):
    """
    Получить документ по ID.
    """
    try:
        result = await es.get(index=INDEX_NAME, id=id)
    except Exception:
        raise HTTPException(status_code=404, detail="Item not found")

    return ReadAPIMatch(id=result["_id"], **result["_source"])


# --------------------
# UPDATE
# --------------------
@router.put("/{id}", response_model=ReadAPIMatch)
async def update_item(id: str, item: ApiMatch, es: AsyncElasticsearch = Depends(get_elastic)):
    """
    Полностью обновить документ.
    """
    exists = await es.exists(index=INDEX_NAME, id=id)
    if not exists:
        raise HTTPException(status_code=404, detail="Item not found")

    await es.update(index=INDEX_NAME, id=id, doc=item.dict())

    return ReadAPIMatch(id=id, **item.dict())


# --------------------
# DELETE
# --------------------
@router.delete("/{id}", response_model=dict)
async def delete_item(id: str, es: AsyncElasticsearch = Depends(get_elastic)):
    """
    Удалить документ по ID.
    """
    exists = await es.exists(index=INDEX_NAME, id=id)
    if not exists:
        raise HTTPException(status_code=404, detail="Item not found")

    result = await es.delete(index=INDEX_NAME, id=id)
    return {"id": id, "result": result["result"]}
