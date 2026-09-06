from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "PeoplePay360"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    API_PREFIX: str = "/api"
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000,"
        "http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175,http://127.0.0.1:3000"
    )

    CONTRACT_EXPIRY_WARNING_DAYS: str = "90,60,30,7"
    CURRENCY: str = "INR"
    TIMEZONE: str = "Asia/Kolkata"

    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 500

    DATABASE_URL: str = "postgresql://postgres:1234@localhost:5432/peoplepay360"
    JWT_SECRET: str = "peoplepay360-dev-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720
    DEMO_PASSWORD: str = "demo123"

    class Config:
        env_file = str(_ENV_FILE)
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def cors_origins_list(self) -> List[str]:
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        extras: List[str] = []
        for origin in origins:
            if "://localhost" in origin:
                extras.append(origin.replace("://localhost", "://127.0.0.1", 1))
            elif "://127.0.0.1" in origin:
                extras.append(origin.replace("://127.0.0.1", "://localhost", 1))
        return list(dict.fromkeys(origins + extras))

    @property
    def expiry_warning_days(self) -> List[int]:
        return [int(d.strip()) for d in self.CONTRACT_EXPIRY_WARNING_DAYS.split(",")]

    @property
    def app_name(self) -> str:
        return self.APP_NAME

    @property
    def app_version(self) -> str:
        return self.APP_VERSION


settings = Settings()
