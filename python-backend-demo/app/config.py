"""Application configuration using Pydantic Settings"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "OrderBuddy API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    PORT: int = 8000

    # Database
    DB_CONN_STRING: str = "mongodb://localhost:27017"
    DB_NAME: str = "orderbuddy"

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"]

    # API Endpoints
    API_ENDPOINT: str = "http://localhost:8000"
    STORE_ENDPOINT: str = "http://localhost:5173"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
