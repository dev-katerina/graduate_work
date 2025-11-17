import os
from logging import config as logging_config
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pydantic import Field
from pathlib import Path

from core.logger import LOGGING
import os

os.makedirs("logs", exist_ok=True)

load_dotenv()


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):
    async_api: str
    elastic_uri: str
    upload_dir: str
    groq_api_key: str
    openai_api_key: str


settings = Settings()
