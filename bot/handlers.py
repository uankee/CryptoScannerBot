from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from loguru import logger

from services.exchanges import exchange_manager
from core.scanner import ArbitrageScanner

router = Router()

@router.message(Command("scan"))
async def cmd_scan(message: Message) -> None:
    await message.answer("🔍 Сканую ринок (Top-5 монет)...")
    
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT"]
    raw_data = await exchange_manager.fetch_tickers(symbols)
    
    results = []
    for symbol in symbols:
        spreads = ArbitrageScanner.calculate_spreads(symbol, raw_data)
        results.extend(spreads)
        
    # для тесту міняти на --- profitable = [opp for opp in results if opp['net_spread'] > -1] ---
    profitable = [opp for opp in results if opp['net_spread'] > 0]
    
    if not profitable:
        await message.answer("📉 Ринки спокійні. Вигідних арбітражних вікон не знайдено.")
        return

    text = "🚀 **Знайдені можливості:**\n\n"
    for opp in profitable:
        text += (f"🔹 **{opp['symbol']}**\n"
                 f"Купити: {opp['buy_on']} @ {opp['buy_price']}\n"
                 f"Продати: {opp['sell_on']} @ {opp['sell_price']}\n"
                 f"Чистий спред: **{opp['net_spread']}%**\n\n")
                 
    await message.answer(text)
    logger.info(f"Відправлено {len(profitable)} сигналів у Telegram.")

@router.message(Command("check"))
async def cmd_check(message: Message) -> None:
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Вкажіть монету. Наприклад: `/check SOL`")
        return
    
    coin = args[1].upper()
    await message.answer(f"⚙️ Перевіряю статус гаманців для **{coin}**...")
    
    status_data = await exchange_manager.fetch_wallet_status(coin)
    
    response = f"📊 **Статус гаманців {coin}:**\n\n"
    for exch, info in status_data.items():
        dep = "✅" if info['deposit'] else "❌"
        wit = "✅" if info['withdraw'] else "❌"
        nets = ", ".join(info['networks']) if info['networks'] else "немає даних"
        
        response += (f"🏛 **{exch.capitalize()}**:\n"
                     f"  Депозит: {dep} | Вивід: {wit}\n"
                     f"  Мережі: {nets}\n\n")
                     
    await message.answer(response)