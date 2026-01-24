import logging
import sys
import asyncio
from fastapi import FastAPI, Depends
from app.config import get_settings, Settings
from app.heath import router as health_router
from contextlib import asynccontextmanager
from app.kafka_consumer import consume_orders 
from app.kafka_producer import kafka_producer
from app.db.engine import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.billing.app.dependency import get_app_settings







@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения, задаем и запускаем задачи до старта нашего приложения 
    и закрываем все сессии и соединения в конце
    """
    # Ниже код, выполняющийся до запуска
    
    settings = get_settings() 
    
    # Настройка логирования
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)] # пишет в stdout, логи в docker всплывают наружу
    )
    logger = logging.getLogger(__name__)
    # выполняется при запуске приложения
    logger.info("Billing service starting...")
    
    engine = create_engine(settings)
    
    
    try: 
        async with engine.begin() as conn: # проверка базы, открываем транзакцию 
            await conn.run_sync(lambda _: None)# "пустой запрос"
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
    
    bg_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    
    consumer_task = asyncio.create_task(
        consume_orders(settings, bg_session_maker)
    )
    
    #запуск producer
    await kafka_producer.start(settings)
    
    #в контейнер приложения заворачиваем наши переиспользуемые функции, чтобы работать с ними в коде через dependency
    app.state.kafka = kafka_producer
    app.state.engine = engine
    app.state.settings = settings
    
    
    
    #до запуска поднимаем consumer в asyncio eventloop как фоновую задачу
    
    yield  # здесь приложение работает
    
    # Код, выполняемый при завершении
    
    consumer_task.cancel()
    
    try:
        await consumer_task # Ждем завершения
    except asyncio.CancelledError:
        logger.info("Consumer task stopped")
        
    await kafka_producer.stop()
    
    #завершение работы producer
    await engine.dispose()#завершение работы бд
    logger.info("Billing service shutting down...")



app = FastAPI(title="Orders Service", version="0.1.0", lifespan=lifespan)


# Подключаем healthcheck
app.include_router(health_router)


#корневой эндпоинт
@app.get("/")
async def root(settings: Settings = Depends(get_app_settings)):
    return {"message": "Billing Service (gRPC soon)","environment": settings.environment}