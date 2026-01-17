from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    kafka_bootstrap_servers: str
    redis_url: str
    log_level: str = "INFO"
    environment: str = "development"

    class Config:
        env_file = Path(__file__).parent.parent.parent.parent / ".env"

settings = Settings()
