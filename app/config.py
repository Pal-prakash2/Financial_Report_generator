from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env."""

    app_name: str = Field(default="FDG Financial Data Service")
    environment: str = Field(default="development")
    database_url: str = Field(
        default="postgresql+psycopg2://fdg:fdg@localhost:5432/fdg",
        description="SQLAlchemy connection string for PostgreSQL.",
    )
    aws_region: str = Field(default="ap-south-1")
    mca_base_url: str = Field(default="https://www.mca.gov.in/XBRLService")
    storage_bucket: Optional[str] = Field(default=None)
    data_dir: Path = Field(default=Path("./data"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached settings instance to avoid re-parsing environment variables."""

    return Settings()
