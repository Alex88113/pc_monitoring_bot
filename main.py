import asyncio
from datetime import datetime

from aiogram import Bot
from loguru import logger

from app.bot.configs.bot_config import settings
from app.bot.handlers.commands import dp


async def main() -> None:
    token = settings.get_token_bot()
    bot = Bot(token=token)

    logger.info(f"Бот запущен в {datetime.now()}")
    try:
        await dp.start_polling(bot)
    finally:
        logger.info(f"Бот остановлен в {datetime.now()}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ValueError as error:
        logger.error(f'В ходе выполнения программы возникла ошибка: {error}')
        raise
    except Exception as error:
        logger.error(f'В ходе выполнения программы произошла непредвиденная ошибка: {error}')
        raise
