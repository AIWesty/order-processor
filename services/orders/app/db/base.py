from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


engine = create_async_engine(
    settings.database_url,
    #echo=True показывает sql в логах, в прод убирать
    pool_pre_ping=True, # проверка соединения перед использованием
    pool_size=10, #базовый пул
    max_overflow=20 # при нагрузке еще до 20 
)


AsyncSessionLocal = async_sessionmaker( 
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False # чтобы объекты оставались доступны после commit
)

#базовый класс для всех моделей, управление метаданными таблиц и сопоставление
class Base(DeclarativeBase):
    pass
