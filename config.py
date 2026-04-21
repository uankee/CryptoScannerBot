from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str
    
    binance_api_key: str | None = None
    binance_secret: str | None = None

    bybit_api_key: str | None = None
    bybit_secret: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()