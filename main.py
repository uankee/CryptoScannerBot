import asyncio
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import settings
from services.exchanges import exchange_manager
from bot.handlers import router
from core.scanner import ArbitrageScanner

bot = Bot(token=settings.bot_token)
dp = Dispatcher()

dp.include_router(router)

@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        f"Арбітражний бот готовий. Ваш Chat ID: `{message.chat.id}`.\n"
        f"Додайте його в .env як ADMIN_CHAT_ID для отримання фонових сповіщень.\n\n"
        f"Натисніть /scan для перевірки ринку."
    )

async def background_scanner():
    if not settings.admin_chat_id:
        logger.warning("ADMIN_CHAT_ID не вказано.")
        return

    logger.info("Фоновий сканер запущено...")

    # 🔽 отримуємо стартовий список
    active_symbols = await exchange_manager.get_common_high_volume_symbols(limit=100)
    last_market_update = asyncio.get_event_loop().time()

    while True:
        try:
            # 🔄 оновлення раз на годину
            current_time = asyncio.get_event_loop().time()
            if current_time - last_market_update > 3600:
                active_symbols = await exchange_manager.get_common_high_volume_symbols(limit=100)
                last_market_update = current_time

            if not active_symbols:
                await asyncio.sleep(10)
                continue

            raw_data = await exchange_manager.fetch_tickers(active_symbols)
            
            results = []
            for symbol in active_symbols:
                spreads = ArbitrageScanner.calculate_spreads(symbol, raw_data)
                results.extend(spreads)
            
            profitable = [opp for opp in results if opp['net_spread'] > 1.2]
            
            if profitable:
                text = "🔔 **АВТО-СКАН: Знайдені можливості!**\n\n"
                for opp in profitable:
                    text += (f"🔹 **{opp['symbol']}**\n"
                             f"Купити: {opp['buy_on']} @ {opp['buy_price']}\n"
                             f"Продати: {opp['sell_on']} @ {opp['sell_price']}\n"
                             f"Чистий спред: **{opp['net_spread']}%**\n\n")

                await bot.send_message(chat_id=settings.admin_chat_id, text=text)
                logger.info(f"Відправлено {len(profitable)} авто-сигналів.")

        except Exception as e:
            logger.error(f"Помилка сканера: {e}")
            
        await asyncio.sleep(30)  # ⏱ частота

async def main() -> None:
    logger.info("Запуск Telegram-бота...")
    asyncio.create_task(background_scanner())
    
    try:
        await dp.start_polling(bot)
    finally:
        await exchange_manager.close_connections()
        await bot.session.close()
        logger.info("З'єднання закрито.")

if __name__ == "__main__":
    logger.add("arbitrage.log", rotation="10 MB", level="INFO")
    asyncio.run(main())