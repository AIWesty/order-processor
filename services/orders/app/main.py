import logging
from fastapi import FastAPI
from app.config import settings
from app.health import router as health_router
from contextlib import asynccontextmanager


# Настройка логирования
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)




@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, выполняемый при запуске
    logger.info("Orders service starting...")
    
    yield  # Здесь приложение работает
    
    # Код, выполняемый при завершении
    logger.info("Orders service shutting down...")



app = FastAPI(title="Orders Service", version="0.1.0", lifespan=lifespan)


# Подключаем healthcheck
app.include_router(health_router)



@app.get("/")
async def root():
    return {"message": "Orders Service", "environment": settings.environment}