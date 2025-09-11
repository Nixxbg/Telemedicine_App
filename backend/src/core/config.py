"""
Core configuration for the telemedicine application
"""

from typing import List, Optional, Union

from pydantic import AnyHttpUrl, ValidationInfo, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """

    # Project
    PROJECT_NAME: str = "Telemedicine App"
    API_V1_STR: str = "/api/v1"

    # Server
    SERVER_NAME: str = "telemedicine-backend"
    SERVER_HOST: AnyHttpUrl = "http://localhost"
    SERVER_PORT: int = 8000

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:8000",  # FastAPI server
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "telemedicine_user"
    POSTGRES_PASSWORD: str = "telemedicine_password"
    POSTGRES_DB: str = "telemedicine"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str):
            return v
        return (
            f"postgresql+asyncpg://{info.data.get('POSTGRES_USER')}:"
            f"{info.data.get('POSTGRES_PASSWORD')}@"
            f"{info.data.get('POSTGRES_SERVER')}:"
            f"{info.data.get('POSTGRES_PORT')}/"
            f"{info.data.get('POSTGRES_DB')}"
        )

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days
    ALGORITHM: str = "HS256"

    # Environment
    ENVIRONMENT: str = "development"

    # JWT
    JWT_SECRET_KEY: str = SECRET_KEY
    JWT_ALGORITHM: str = ALGORITHM

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
