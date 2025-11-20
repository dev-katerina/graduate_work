from fastapi import APIRouter, Query, Depends, File, UploadFile

from services import async_api, decision_maker
from core.config import settings
import os
from connections import whisper_service, elastic
from services.async_api import search_films



router = APIRouter()

@router.post("/question/")
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
@router.post("/question_text/")
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