"""Configuration from environment variables.

A local `.env` file (see `.env.example`) is loaded if present. Real
environment variables always win over the file, so Docker/CI settings are
never overridden by a stray .env.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str


def get_settings() -> Settings:
    # Read on every call (not at import) so tests can change the environment.
    return Settings(
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=int(os.getenv("DB_PORT", "5432")),
        db_name=os.getenv("DB_NAME", "recruiterflow"),
        db_user=os.getenv("DB_USER", "postgres"),
        db_password=os.getenv("DB_PASSWORD", ""),
    )
