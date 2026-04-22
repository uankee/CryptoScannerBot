from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from loguru import logger

from config import settings
from services.exchanges import exchange_manager
from core.scanner import ArbitrageScanner

router = Router()

@router.message(Command("scan"))
async def cmd_scan(message: Message) -> None:
    await message.answer("🔄 Збираю актуальні високоліквідні монети...")
    
    # 🔽 динамічний список
    active_symbols = await exchange_manager.get_common_high_volume_symbols(limit=50)
    
    if not active_symbols:
        await message.answer("❌ Помилка: не вдалося отримати список спільних пар.")
        return

    await message.answer(f"🔍 Сканую ринок ({len(active_symbols)} монет)...")
    
    raw_data = await exchange_manager.fetch_tickers(active_symbols)
    
    results = []
    for symbol in active_symbols:
        spreads = ArbitrageScanner.calculate_spreads(
            symbol=symbol,
            exchange_data=raw_data,
            trading_fee_pct=settings.trading_fee_pct,
            withdrawal_fee_pct=settings.withdrawal_fee_pct,
        )
        results.extend(spreads)
        
    profitable = [opp for opp in results if opp['net_spread'] > settings.profit_threshold]
    
    if not profitable:
        await message.answer("📉 Ринки спокійні. Вигідних арбітражних вікон не знайдено.")
        return
        
    # 🔽 сортування + топ 10
    response = "🚀 **Знайдені можливості:**\n\n"
    for opp in sorted(profitable, key=lambda x: x['net_spread'], reverse=True)[:10]:
        response += (f"🔹 **{opp['symbol']}**\n"
                     f"Купити: {opp['buy_on']} @ {opp['buy_price']}\n"
                     f"Продати: {opp['sell_on']} @ {opp['sell_price']}\n"
                     f"Gross: {opp['gross_spread']}% | Комісії: {opp['fees']}%\n"
                     f"Чистий спред: **{opp['net_spread']}%**\n\n")
                     
    await message.answer(response)
    logger.info(f"Відправлено {len(profitable)} сигналів.")

@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    await message.answer(
        "⚙️ Поточні налаштування:\n"
        f"- Profit threshold: **{settings.profit_threshold}%**\n"
        f"- Trading fee: **{settings.trading_fee_pct}%**\n"
        f"- Withdrawal fee: **{settings.withdrawal_fee_pct}%**\n\n"
        "Щоб змінити — оновіть `.env` і перезапустіть бота."
    )

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
