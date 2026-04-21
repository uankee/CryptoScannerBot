import asyncio
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import settings
from services.exchanges import exchange_manager
from bot.handlers import router

bot = Bot(token=settings.bot_token)
dp = Dispatcher()

# Підключаємо наші команди
dp.include_router(router)

@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer("Арбітражний бот готовий. Натисни /scan для перевірки ринку.")

async def main() -> None:
    logger.info("Запуск Telegram-бота...")
    try:
        await dp.start_polling(bot)
    finally:
        await exchange_manager.close_connections()
        await bot.session.close()
        logger.info("З'єднання закрито.")

if __name__ == "__main__":
    logger.add("arbitrage.log", rotation="10 MB", level="INFO")
    asyncio.run(main())