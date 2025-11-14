from fastapi import FastAPI, File, UploadFile
from contextlib import asynccontextmanager
from connections import whisper_service, elastic
import whisper
import os
from services import async_api, decision_maker
from elasticsearch import AsyncElasticsearch
from core.config import settings
from fastapi import Depends


@asynccontextmanager
async def lifespan(app: FastAPI):
    whisper_service.model = whisper.load_model("turbo")
    elastic.es = AsyncElasticsearch(hosts=[settings.elastic_uri])

    yield
    await elastic.es.close()


app = FastAPI(lifespan=lifespan)

os.makedirs(settings.upload_dir, exist_ok=True)


@app.post("/upload_audio/")
async def upload_audio(
    file: UploadFile = File(...),
    dm: decision_maker.DecisionMaker = Depends(decision_maker.get_decision_maker),
):
    # === 1. Сохраняем файл ===
    file_path = os.path.join(settings.upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # === 2. Транскрипция ===
    result = whisper_service.model.transcribe(file_path)
    text = result["text"].strip()

    # === 3. Поиск подходящего эндпоинта ===
    uri_info = await dm.choose_uri(text)
    if not uri_info:
        return {
            "voice": "Извините, не удалось определить запрос",
            "text": text,
        }

    # === 4. Извлечение параметров из текста ===

    extracted_params = await dm.get_parameters(uri_info, text)

    # === 5. Возврат результата для проверки ===
    return {
        "recognized_text": text,
        "api_uri": uri_info.api_uri,
        "voice_form": uri_info.voice_form,
        "text_form": uri_info.text_form,
        "parameters": uri_info.parameters,
        "extracted_parameters": extracted_params,
    }