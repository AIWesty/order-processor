from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings


settings = get_settings()

engine = create_async_engine(
    settings.database_url,  #живем в базе orders, в проде создали бы новую
    pool_pre_ping=True,#включаем тестовый запрос на проверку соединения(каждого коннекта)
    pool_size=5,
    max_overflow=10
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False #разрешает переиспользовать обьекты без повторного запроса к бд о их состоянии
)

class Base(DeclarativeBase): #описываем базовый класс для моделей
    pass

