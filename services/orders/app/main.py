import logging
import sys
import asyncio
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.config import get_settings, Settings
from app.health import router as health_router
from app.api.orders import router as orders_router 
from app.db.engine import create_engine 
from contextlib import asynccontextmanager
from app.kafka_producer import kafka_client
from app.dependency import get_app_settings 
from app.kafka_consumer import consume_payment_events
from app.grpc_client import BillingGrpcClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения, задаем и запускаем задачи до старта нашего приложения 
    и закрываем все сессии и соединения в конце
    """
    # Ниже код, выполняющийся до запуска
    
    #получаем конфиг с настройками
    settings = get_settings()
    
    #настройка логирования
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)] # пишет в stdout, логи в docker всплывают наружу
        )
    logger = logging.getLogger(__name__)
    
    logger.info("Orders service starting...")
    logger.info(f"Database URL: {settings.database_url}")
    
    
    #получаем движок 
    engine = create_engine(settings) 
    try:
        async with engine.begin() as conn: #начинаем транзакцию
            await conn.run_sync(lambda _: None) # выполняем пустой запрос к базе для проверки работы
            logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
    #своя фабрика для фоновых задач, которые обьявляем ниже 
    bg_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    #встраиваем consumer в event loop
    consumer_task = asyncio.create_task(
        consume_payment_events(settings, bg_session_maker)
    )
    
    await kafka_client.start(settings) # поднимаем producer kafka
    
    billing_client = BillingGrpcClient(settings)
    await billing_client.connect()
    
    
    #в контейнер приложения заворачиваем наши переиспользуемые функции, чтобы работать с ними в коде через dependency
    app.state.kafka = kafka_client 
    app.state.engine = engine
    app.state.settings = settings
    app.state.billing_client = billing_client
    
    yield  # отдаем управление приложению 
    
    # Код, выполняемый при завершении
    consumer_task.cancel() 
    try:
        await consumer_task # Ждем завершения
    except asyncio.CancelledError:
        logger.info("Consumer task stopped")
        
    await kafka_client.stop()
    await billing_client.close()
    await engine.dispose() #закрытие соединений после завершения работы приложения 
    logger.info("Database conn closed")
    logger.info("Orders service shutting down...")



app = FastAPI(title="Orders Service", version="0.1.0", lifespan=lifespan)


# Подключаем healthcheck
app.include_router(health_router)
app.include_router(orders_router)



# Служебный endpoint, располагается на /
@app.get("/")
async def root(settings: Settings = Depends(get_app_settings)):
    return {
        "message": "Orders Service",
        "environment": settings.environment,
        "endpoints": ['/health', '/orders']
    }
    
