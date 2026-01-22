import pytest
import asyncio
from testcontainers.postgres import PostgresContainer
from testcontainers.kafka import KafkaContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient


import os 
import sys
sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..")))# для импорта из orders, создаем путь для поиска модулей(добавляем в начало sys.path)\


from services.orders.app.db.base import Base
from services.orders.app.config import settings

@pytest.fixture(scope="session")
def event_loop(): 
    """Переопределение event_loop для использования одного цикла на всю сессию"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop #отдаем в тест цикл
    loop.close() #завершает работу event_loop и освобождает память и ресурсы
    
@pytest.fixture(scope="session")
async def postgres_container(): 
    """Создание контейнера для базы данных"""
    with PostgresContainer("postgres:16-alpine") as postgres_container:
        yield postgres_container
        

@pytest.fixture(scope="session")
async def kafka_container():
    """Создание контейнера для кафка"""
    with KafkaContainer() as Kafka: 
        yield Kafka
    
@pytest.fixture(scope="session")
async def test_db_engine(postgres_container): 
    """Создаем движок для тестовой базы"""
    db_url = postgres_container.get_connection_url().replace("psycopg2", 'asyncpg')#цепляем с контейнера url подключения 
    engine = create_async_engine(db_url, echo=True)#создаем движок
    
    async with engine.begin() as conn: #открываем транзакцию
        await conn.run_sync(Base.metadata.create_all)#создаем таблицы из метаданных 
        
    yield engine #отдаем движок для передачи в сессии
    
    await engine.dispose()#закрываем соединение после 
    
@pytest.fixture
async def test_db_session(test_db_engine): 
    """Сессии для тестов (каждый тест получает свою уникальную сессию)"""
    SessionLocal = async_sessionmaker(test_db_engine, class_=AsyncSession, expire_on_commit=False)#создаем класс фабрики сессий
    async with SessionLocal() as session: #создаем сессию и отдаем ее
        yield session
        
    
@pytest.fixture
async def test_client(test_db_engine, kafka_container, monkeypatch):
    """HTTP клиент для FastAPI с подменой настроек"""
    db_url = test_db_engine.url.render_as_string(hide_password=False) #строчка подключения
    monkeypatch.setattr(settings, 'database_url', db_url)#патчим переменные окружения, здесь пожключение к бд
    monkeypatch.setattr(settings, "kafka_bootstrap_servers", kafka_container.get_bootstrap_server()) #здесь меняем брокера кафки
    
    async with AsyncClient(base_url="http://test") as client: #открываем HTTP подключение
        yield client#выбрасываем доступ к нему в поток программы