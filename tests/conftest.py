import pytest
import asyncio
import os 
import sys
from typing import AsyncGenerator
from testcontainers.postgres import PostgresContainer
from testcontainers.kafka import KafkaContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

#добавляем корень проекта на всякий случай для корректного импортирования 
project_root = os.path.dirname(os.path.dirname(__file__))      # order-processor
service_root = os.path.join(project_root, "services", "orders") # services/orders
sys.path.insert(0, service_root)

from app.main import app as real_app
from app.db.base import Base
from app.config import Settings
from app.kafka_producer import kafka_client
from app.dependency import get_app_settings, get_db


    
@pytest.fixture(scope="session")
def postgres_container(): 
    """Создание контейнера для базы данных"""
    with PostgresContainer("postgres:16-alpine") as postgres_container:
        yield postgres_container
        

@pytest.fixture(scope="session")
def kafka_container():
    """Создание контейнера для кафка"""
    with KafkaContainer() as Kafka: 
        yield Kafka
    
@pytest.fixture
async def test_db_engine(postgres_container) -> AsyncGenerator: 
    """Создаем движок для тестовой базы и поднимаем схему"""
    db_url = postgres_container.get_connection_url().replace("psycopg2", 'asyncpg')#цепляем с контейнера url подключения 
    engine = create_async_engine(db_url, echo=True)#создаем движок
    
    async with engine.begin() as conn: #открываем транзакцию
        await conn.run_sync(Base.metadata.create_all)#создаем таблицы из метаданных 
        
    yield engine #отдаем движок для передачи в сессии
    
    # После всех тестов
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    
@pytest.fixture 
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]: 
    """Сессии для тестов (каждый тест получает свою уникальную сессию)"""
    SessionLocal = async_sessionmaker(test_db_engine, class_=AsyncSession, expire_on_commit=False)#создаем класс фабрики сессий
    async with SessionLocal() as session: #создаем сессию и отдаем ее
        yield session
        
    
@pytest.fixture
async def test_app(test_db_engine, kafka_container) -> AsyncGenerator:
    """
    тестовое приложение FastAPI с подмененными зависимостями:
    database_url указывает на testcontainers Postgres
    kafka_bootstrap_servers указывает на testcontainers Kafka
    get_db отдает сессию поверх test_db_engine
    """
    
    #руками создаем "моковые" данные для окружения(используем в переопределнии)
    test_settings = Settings(
        database_url=test_db_engine.url.render_as_string(hide_password=False), #берем url из движка
        postgres_user="test",        # не обязательно, но можно заполнить
        postgres_password="test",
        postgres_db="test",
        kafka_bootstrap_servers=kafka_container.get_bootstrap_server(),
        redis_url="redis://test",    # если нужно
        log_level="DEBUG",
        environment="test",
    )
    
    #для переопределения получения настроек
    def override_get_app_settings():
        return test_settings

    #переопределяем получение сессии
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]: 
        #фабрика сесии
        SessionLocal = async_sessionmaker(test_db_engine, class_=AsyncSession, expire_on_commit=False)
        async with SessionLocal() as session:
            try:
                yield session #открываем и выбрасываем сесиию в приложение 
            except Exception:
                raise
    #применияем переопределение зависимостей
    real_app.dependency_overrides[get_app_settings] = override_get_app_settings
    real_app.dependency_overrides[get_db] = override_get_db
    
    #стартуем producer кафки
    await kafka_client.start(test_settings)
    try: 
        yield real_app#выбрасываем приложение в программу
    finally: 
        real_app.dependency_overrides.clear()#в конце чистим переопределения и останавливаем кафку
        await kafka_client.stop()
        
@pytest.fixture
async def test_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """
    асинхронный HTTP-клиент для обращения к FastAPI в тестах
    Lifespan приложения уже подхватывается FastAPI/ASGI при первом запросе
    """
    transport = ASGITransport(app=test_app)#транспортный слой, вызывает asgi и эмулирует запросы
    async with AsyncClient(transport=transport, base_url="http://test") as client: #создаем клиента для запросов
        yield client 
