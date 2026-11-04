"""Centralised configuration - loads .env once, exposes typed settings."""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "enterprise_ai_backend")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_VERSION: str = os.getenv("APP_VERSION", "0.3.0")

    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"

    # Real SQLite DB for local / default. In Azure, DATABASE_URL points at Postgres.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./data/enterprise_ai.db",
    )
    # Hosted Postgres (Railway, Heroku, etc.) hands out postgres:// or
    # postgresql:// URLs; SQLAlchemy needs the psycopg3 dialect spelled out.
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgres://"):]
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgresql://"):]

    # Auth
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET",
        "dev-only-change-me-" + ("x" * 40),
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRES_MINUTES: int = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))

    # CORS
    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "*").split(",")
        if o.strip()
    ]


settings = Settings()
