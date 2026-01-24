
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str # живем в базе orders, в проде создали бы новую
    kafka_bootstrap_servers: str
    redis_url: str
    log_level: str = "INFO"
    environment: str = "development"

    class Config:
        env_file = Path(__file__).parent / ".env"


def get_settings() -> Settings:
    """
    Ленивая загрузка, использовать в точках входа, не использовать в обычных модулях. 
    Избегать циклического импорта
    """
    return Settings() # type: ignore , работает правильно 