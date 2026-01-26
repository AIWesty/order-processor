from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    
    billing_grpc_host: str = "billing"
    billing_grpc_port: int = 50051
    
    kafka_bootstrap_servers: str
    redis_url: str
    log_level: str = "INFO"
    environment: str = "development"

    class Config:
        env_file = Path(__file__).parent / ".env"


@lru_cache
def get_settings() -> Settings:
    """
    Ленивая загрузка, использовать в точках входа, не использовать в обычных модулях. 
    Избегать циклического импорта
    """
    return Settings() # type: ignore , работает правильно 
