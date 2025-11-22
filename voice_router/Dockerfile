FROM python:3.10

# Создаем рабочую директорию
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg

# Копируем зависимости и устанавливаем
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь src внутрь /app/app
COPY src/ .

# Команда запуска
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]

