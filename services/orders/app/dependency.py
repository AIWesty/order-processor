from typing import AsyncGenerator
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.config import Settings
from app.kafka_producer import KafkaProducerClient

def get_app_settings(request: Request) -> Settings: 
    """Зависимость для использования настроек в эндпоинтах"""
    return request.app.state.settings


def get_kafka_producer(request: Request) -> KafkaProducerClient:
    """Зависимость Kafka"""
    return request.app.state.kafka

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]: 
    """Зависимость для получения сессии базы данных"""
    engine = request.app.state.engine #берем из данных который загрузили при старте
    
    
    #создание фабрики сессий
    session_maker = async_sessionmaker(
        engine, 
        class_=AsyncSession,
        expire_on_commit=False #оставляет сведения об обьекте после commit
    )
    
    async with session_maker() as session: #фабрикой создаем сессию 
        try: 
            yield session # пытаемся прокинуть сессию в приложение для взаимодействия
            await session.commit() #как получаем управление сохраняем изменения 
        except Exception: 
            await session.rollback() #ошибка - откат транзакции 
            raise
        finally: 
            await session.close() #формальность, тк контекстный закроет
            
    