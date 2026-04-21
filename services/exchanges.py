import asyncio
import ccxt.async_support as ccxt
from loguru import logger
from typing import Dict, Any
from config import settings

class ExchangeManager:
    def __init__(self) -> None:
        # Тут ми передаємо ключі з config.py безпосередньо в CCXT
        self.exchanges = {
            "binance": ccxt.binance({
                'apiKey': settings.binance_api_key,
                'secret': settings.binance_secret,
                'enableRateLimit': True
            }),
            "bybit": ccxt.bybit({
                'apiKey': settings.bybit_api_key,
                'secret': settings.bybit_secret,
                'enableRateLimit': True
            }),
            "okx": ccxt.okx({'enableRateLimit': True}),
            "mexc": ccxt.mexc({'enableRateLimit': True})
        }

    async def fetch_tickers(self, symbols: list[str]) -> Dict[str, Dict[str, Any]]:
        tasks = []
        exchange_names = []
        for name, exchange in self.exchanges.items():
            tasks.append(exchange.fetch_tickers(symbols))
            exchange_names.append(name)
        
        logger.info("Запуск конкурентного запиту тікерів...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        data = {}
        for name, result in zip(exchange_names, results):
            if isinstance(result, Exception):
                logger.error(f"Помилка тікерів {name}: {result}")
                data[name] = {}
            else:
                data[name] = result
        return data

    async def fetch_wallet_status(self, symbol: str) -> Dict[str, Any]:
        """Гібридний метод: реальні дані + заглушка для решти."""
        coin = symbol.split('/')[0] if '/' in symbol else symbol
        
        mock_networks = {
            "binance": ["ERC20", "TRC20", "BEP20"],
            "okx": ["ERC20", "SOL", "TRC20"],
            "mexc": ["BEP20"]
        }

        tasks = []
        exchange_names = []
        for name, exchange in self.exchanges.items():
            if exchange.apiKey and "optional" not in exchange.apiKey:
                tasks.append(exchange.fetch_currencies())
            else:
                tasks.append(asyncio.sleep(0)) 
            exchange_names.append(name)

        logger.info(f"Запит статусів гаманця для {coin}...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        status_data = {}
        for name, result in zip(exchange_names, results):
            # Додаємо логування помилок для реальних API-запитів
            if isinstance(result, Exception):
                logger.error(f"Помилка гаманців {name}: {result}")
                
            if result is not None and not isinstance(result, Exception):
                coin_data = result.get(coin, {})
                status_data[name] = {
                    "deposit": coin_data.get('deposit', True),
                    "withdraw": coin_data.get('withdraw', True),
                    "networks": list(coin_data.get('networks', {}).keys()) if coin_data.get('networks') else []
                }
            else:
                status_data[name] = {
                    "deposit": True, "withdraw": True,
                    "networks": mock_networks.get(name, [])
                }
        return status_data

    async def close_connections(self) -> None:
        for exchange in self.exchanges.values():
            await exchange.close()

# Екземпляр створюється поза класом
exchange_manager = ExchangeManager()