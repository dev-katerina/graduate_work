from fastapi import FastAPI, File, UploadFile
from contextlib import asynccontextmanager
import whisper
import os
from services import whisper_service, async_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    whisper_service.model = whisper.load_model("turbo")
    yield


app = FastAPI(lifespan=lifespan)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)



@app.post("/upload_audio/")
async def upload_audio(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Транскрибируем аудио
    result = whisper_service.model.transcribe(file_path)
    text = result["text"]

    # Отправляем запрос на поиск фильмов
    films = await async_api.search_films(text)

    return {"voice": "", "text": "", "films": films}
