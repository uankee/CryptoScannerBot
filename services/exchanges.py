import asyncio
from typing import Dict, List, Any, Set
import ccxt.async_support as ccxt
from loguru import logger
from config import settings

class ExchangeManager:
    def __init__(self) -> None:
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
                    "deposit": True,
                    "withdraw": True,
                    "networks": mock_networks.get(name, [])
                }
        return status_data

    # 🔽 НОВИЙ МЕТОД
    async def get_common_high_volume_symbols(self, limit: int = 100) -> List[str]:
        """Знаходить спільні символи між біржами, фільтруючи за об'ємом на Binance."""
        try:
            logger.info("Оновлення списку активних символів...")
            
            # Завантаження маркетів
            await asyncio.gather(*[ex.load_markets() for ex in self.exchanges.values()])
            
            binance = self.exchanges.get('binance')
            if not binance:
                return []
                
            tickers = await binance.fetch_tickers()

            # Топ по об'єму
            usdt_pairs = [
                (s, t['quoteVolume']) for s, t in tickers.items()
                if s.endswith('/USDT') and t.get('quoteVolume')
            ]
            top_pairs = sorted(usdt_pairs, key=lambda x: x[1], reverse=True)[:limit]
            top_symbols = {p[0] for p in top_pairs}

            # Перетин бірж
            common_symbols = top_symbols
            for name, ex in self.exchanges.items():
                if name == 'binance':
                    continue
                ex_symbols = set(ex.symbols)
                common_symbols = common_symbols.intersection(ex_symbols)

            logger.info(f"Знайдено {len(common_symbols)} спільних активних пар.")
            return list(common_symbols)

        except Exception as e:
            logger.error(f"Помилка при пошуку символів: {e}")
            return []

    async def close_connections(self) -> None:
        for exchange in self.exchanges.values():
            await exchange.close()

# екземпляр
exchange_manager = ExchangeManager()