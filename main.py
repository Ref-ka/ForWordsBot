import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
from handlers import add_word, common, edit_words, export_words, flashcards, reminders, show_words
from utils.database import DataBase


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    db = DataBase()

    dp = Dispatcher(storage=MemoryStorage())

    dp["db"] = db

    bot = Bot(token=config.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp.include_routers(
        common.router,
        add_word.router,
        edit_words.router,
        export_words.router,
        flashcards.router,
        reminders.router,
        show_words.router
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
