from pydantic import EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    GMAIL_ADDRESS: EmailStr
    GMAIL_PASSWORD: SecretStr

    USER_ID: int
    RELEASE_RADAR_ID: str
    SPOTIFY_CLIENT_BASE_64: str
    SPOTIFY_REFRESH_TOKEN: str


settings = Settings()
