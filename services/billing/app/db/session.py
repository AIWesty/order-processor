from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import AsyncSessionLocal

#зависимость для прокидывания сессии в логику
async def get_db() -> AsyncGenerator[AsyncSession, None]: 
    async with AsyncSessionLocal() as session: #создаем обьект asyncsession и работаем с ней
        try: 
            yield session # отдаем сессию и управление в логику
            await session.commit()#принудительно комитим изменения 
        except Exception as e: 
            await session.rollback() #при ошибка откатываем изменения 
            raise e #прокидываем выше исключение 
        finally: 
            await session.close()# закрытие сессии в конце