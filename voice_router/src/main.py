from fastapi import FastAPI, File, UploadFile
from contextlib import asynccontextmanager
from connections import whisper_service, elastic
import whisper
import os
from elasticsearch import AsyncElasticsearch
from core.config import settings
from api.v1 import user, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    whisper_service.model = whisper.load_model("turbo")
    elastic.es = AsyncElasticsearch(hosts=[settings.elastic_uri])

    yield
    await elastic.es.close()


app = FastAPI(lifespan=lifespan)

os.makedirs(settings.upload_dir, exist_ok=True)
app.include_router(user.router, prefix="/api/v1", tags=["Поиск фильмов"])
app.include_router(admin.router, prefix="/api/v1", tags=["Редактирование навыка"])
