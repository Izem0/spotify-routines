from pathlib import Path

from pydantic import EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
DOT_ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=DOT_ENV_FILE, env_ignore_empty=True, extra="ignore"
    )

    GMAIL_ADDRESS: EmailStr
    GMAIL_PASSWORD: SecretStr

    USER_ID: int
    RELEASE_RADAR_ID: str
    SPOTIFY_CLIENT_BASE_64: str
    SPOTIFY_REFRESH_TOKEN: str


settings = Settings()
