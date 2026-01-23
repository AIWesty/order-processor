from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    
    kafka_bootstrap_servers: str
    redis_url: str
    log_level: str = "INFO"
    environment: str = "development"

    class Config:
        env_file = Path(__file__).parent / ".env"


@lru_cache
def get_settings() -> Settings:
    """Ленивая загрузка только тогда, когда нужно"""
    return Settings() # type: ignore , работает правильно 
