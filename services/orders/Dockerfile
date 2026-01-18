FROM python:3.13-slim

WORKDIR /app

# Установка curl для healthcheck
RUN apt-get update && apt-get install -y curl postgresql-client && rm -rf /var/lib/apt/lists/*

#копируем файл с зависимостями и ставим перед приложением, чтобы закешировать слой
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

#копируем приложение в рабочую директорию
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

#запускаем asgi сервер и миграции
CMD sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"