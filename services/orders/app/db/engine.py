from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from app.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Создается единожды при старте приложения"""
    return create_async_engine(
        settings.database_url,
        #echo=True показывает sql в логах, в прод убирать
        pool_pre_ping=True, # проверка соединения перед использованием (health check для pool)
        pool_size=10, #базовый пул
        max_overflow=20, # при нагрузке еще до 20
        echo=(settings.log_level == "DEBUG"),
    )


