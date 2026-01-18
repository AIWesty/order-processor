FROM python:3.13-slim

WORKDIR /app

# Установка curl для healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

#копируем файл с зависимостями и ставим перед приложением, чтобы закешировать слой
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

#копируем приложение в рабочую директорию
COPY app/ ./app/

#запускаем asgi сервер
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]