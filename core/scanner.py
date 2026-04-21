from typing import Dict, List, Any

class ArbitrageScanner:
    @staticmethod
    def calculate_spreads(symbol: str, exchange_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        prices = []

        # Збираємо ціни з усіх бірж
        for exch_name, tickers in exchange_data.items():
            if symbol in tickers and tickers[symbol].get('last'):
                prices.append({
                    "exchange": exch_name,
                    "price": tickers[symbol]['last']
                })

        # Якщо < 2 бірж — нема арбітражу
        if len(prices) < 2:
            return []

        # Сортування
        sorted_prices = sorted(prices, key=lambda x: x['price'])
        min_node, max_node = sorted_prices[0], sorted_prices[-1]

        # Спред
        gross_spread_pct = (max_node['price'] - min_node['price']) / min_node['price'] * 100
        net_spread_pct = gross_spread_pct - 0.2  # комісії

        return [{
            "symbol": symbol,
            "buy_on": min_node['exchange'],
            "buy_price": min_node['price'],
            "sell_on": max_node['exchange'],
            "sell_price": max_node['price'],
            "net_spread": round(net_spread_pct, 2)
        }]