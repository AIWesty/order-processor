import logging
import sys
import asyncio
from fastapi import FastAPI
from app.config import settings
from app.heath import router as health_router
from contextlib import asynccontextmanager
from app.kafka_consumer import consume_orders 
from app.kafka_producer import kafka_producer
from app.db.base import engine


# Настройка логирования
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)] # пишет в stdout, логи в docker всплывают наружу
)
logger = logging.getLogger(__name__)




@asynccontextmanager
async def lifespan(app: FastAPI):
    # выполняется при запуске приложения
    logger.info("Billing service starting...")
    
    
    try: 
        async with engine.begin() as conn: # проверка базы, открываем транзакцию 
            await conn.run_sync(lambda _: None)# "пустой запрос"
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
    #запуск producer
    await kafka_producer.start()
    
    #до запуска поднимаем consumer в asyncio eventloop как фоновую задачу
    task = asyncio.create_task(consume_orders())
    
    yield  # здесь приложение работает
    
    
    # Код, выполняемый при завершении
    #завершение работы producer
    await kafka_producer.stop()
    await engine.dispose()#завершение работы бд
    logger.info("Billing service shutting down...")



app = FastAPI(title="Orders Service", version="0.1.0", lifespan=lifespan)


# Подключаем healthcheck
app.include_router(health_router)


#корневой эндпоинт
@app.get("/")
async def root():
    return {"message": "Billing Service (gRPC soon)","environment": settings.environment}