import logging
import sys
from fastapi import FastAPI
from app.config import settings
from app.health import router as health_router
from app.api.orders import router as orders_router 
from contextlib import asynccontextmanager
from app.db.base import engine
from kafka_producer import kafka_client


# Настройка логирования
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)] # пишет в stdout, логи в docker всплывают наружу
)
logger = logging.getLogger(__name__)




@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, выполняемый при запуске
    logger.info("Orders service starting...")
    logger.info(f"Database URL: {settings.database_url}")
    
    try: #попытка проверки коннекта к базе с пустым сообщением
        async with engine.begin() as conn: #начинаем транзакцию
            await conn.run_sync(lambda _: None)
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
    await kafka_client.start() # поднимаем клиент кафки
    
    yield  # отдаем управление приложению 
    
    # Код, выполняемый при завершении
    logger.info("Orders service shutting down...")
    await kafka_client.stop()
    await engine.dispose()
    logger.info("Database conn closed")



app = FastAPI(title="Orders Service", version="0.1.0", lifespan=lifespan)


# Подключаем healthcheck
app.include_router(health_router)
app.include_router(orders_router)


@app.get("/")
async def root():
    return {
        "message": "Orders Service",
        "environment": settings.environment,
        "endpoints": ['/health', '/orders']
    }
    
