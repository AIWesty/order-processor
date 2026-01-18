from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import AsyncSessionLocal


#зависимость для Fastapi, для использования сессии бд в эндпоинте 
async def get_db() -> AsyncGenerator[AsyncSession, None]: 
    async with AsyncSessionLocal() as session: # вызываем в переменную session создание асинхронной сессии
        try: 
            yield session # выбрасываем сессию на пользование 
            await session.commit() #если нет ошибок сохраняем изменения в базу
        except Exception as e : 
            await session.rollback() #откатываем транзакцию если есть исключения 
            raise e # прокидываем исключение выше
        finally:
            await session.close() # закрываем сессию всегда 