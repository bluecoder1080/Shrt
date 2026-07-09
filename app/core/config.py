from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "URL Shortener API"
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    RATE_LIMIT_SHORTEN_WINDOW: int = 60
    RATE_LIMIT_SHORTEN_MAX_REQUESTS: int = 20
    RATE_LIMIT_REDIRECT_WINDOW: int = 60
    RATE_LIMIT_REDIRECT_MAX_REQUESTS: int = 120
    
    ALLOWED_ORIGINS: Union[str, List[str]]
    
    # Celery & RabbitMQ
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # GeoIP Path
    GEOIP_DATABASE_PATH: str = "app/resources/GeoLite2-Country.mmdb"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

settings = Settings()
