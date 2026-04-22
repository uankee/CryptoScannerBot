from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str
    admin_chat_id: int | None = None 
    profit_threshold: float = 1.5
    trading_fee_pct: float = 0.1
    withdrawal_fee_pct: float = 0.1
    
    binance_api_key: str | None = None
    binance_secret: str | None = None

    bybit_api_key: str | None = None
    bybit_secret: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
