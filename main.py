import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart

from db.engine import create_db, drop_db, session_maker
from handlers.basic import get_product_info, start_command_handler, basic_router
from settings import TOKEN, COMMANDS_LIST
from middlewares.db import DataBaseSession


async def start():
    bot = Bot(token=TOKEN, default=DefaultBotProperties())

    dp = Dispatcher()

    dp.include_router(basic_router)

    await create_db()

    dp.update.middleware(DataBaseSession(session_maker=session_maker))
    await bot.set_my_commands(commands=COMMANDS_LIST)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(start())
