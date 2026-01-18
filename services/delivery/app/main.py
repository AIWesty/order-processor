import logging
import sys
from fastapi import FastAPI
from app.config import settings
from app.health import router as health_router
from contextlib import asynccontextmanager

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]  # пишет в stdout, логи в docker всплывают наружу
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, выполняемый при запуске
    logger.info("Delivery service starting (Kafka consumer soon)...")
    
    yield  # Здесь приложение работает
    
    # Код, выполняемый при завершении
    logger.info("Delivery service shutting down...")



app = FastAPI(title="Delivery Service", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)


@app.get("/")
async def root():
    return {"message": "Delivery Service (Kafka consumer)", "environment": settings.environment}
