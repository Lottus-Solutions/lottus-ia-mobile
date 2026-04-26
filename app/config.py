import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _parse_cors_origins(raw_origins: str | None) -> list[str]:
    if not raw_origins:
        return ["*"]

    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or ["*"]


@dataclass(slots=True)
class Settings:
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    gemini_api_key: str | None
    gemini_model: str
    cors_origins: list[str]

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            db_host=os.getenv("DB_HOST", "localhost"),
            db_port=int(os.getenv("DB_PORT", "3306")),
            db_user=os.getenv("DB_USER", "root"),
            db_password=os.getenv("DB_PASSWORD", ""),
            db_name=os.getenv("DB_NAME", "lottusdb"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            cors_origins=_parse_cors_origins(os.getenv("CORS_ORIGINS")),
        )
