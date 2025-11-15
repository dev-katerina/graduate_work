from fastapi import FastAPI, File, UploadFile
from contextlib import asynccontextmanager
from connections import whisper_service, elastic
import whisper
import os
from services import async_api, decision_maker
from elasticsearch import AsyncElasticsearch
from core.config import settings
from fastapi import Depends
from services.async_api import search_films


@asynccontextmanager
async def lifespan(app: FastAPI):
    whisper_service.model = whisper.load_model("turbo")
    elastic.es = AsyncElasticsearch(hosts=[settings.elastic_uri])

    yield
    await elastic.es.close()


app = FastAPI(lifespan=lifespan)

os.makedirs(settings.upload_dir, exist_ok=True)

# ======= АУДИО ВЕРСИЯ =======
@app.post("/question/")
async def upload_audio(
    file: UploadFile = File(...),
    dm: decision_maker.DecisionMaker = Depends(decision_maker.get_decision_maker),
):
    # 1. Сохраняем файл
    file_path = os.path.join(settings.upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # 2. Транскрипция
    result = whisper_service.model.transcribe(file_path)
    text = result["text"].strip()

    # 3. Поиск эндпоинта
    uri_info = await dm.choose_uri(text)
    if not uri_info:
        return {
            "voice": "Извините, не удалось определить запрос",
            "text": text,
        }

    # 4. Извлечение параметров
    extracted_params = await dm.get_parameters(uri_info, text)

    res = await search_films(uri_info, extracted_params)

    # 5. Ответ
    return {
        "voice_form": uri_info.voice_form,
        "films": res,
    }


# ======= ТЕКСТОВАЯ ВЕРСИЯ (НОВАЯ) =======
@app.post("/question_text/")
async def process_text(
    text: str,
    dm: decision_maker.DecisionMaker = Depends(decision_maker.get_decision_maker),
):
    text = text.strip()

    # 1. Определяем эндпоинт
    uri_info = await dm.choose_uri(text)
    if not uri_info:
        return {
            "voice": "Извините, не удалось определить запрос",
            "text": text,
        }

    # 2. Извлекаем параметры
    extracted_params = await dm.get_parameters(uri_info, text)

    # 3. Выполняем поиск
    res = await search_films(uri_info, extracted_params)

    # 4. Возврат
    return {
        "text_form": uri_info.text_form,
        "films": res,
    }