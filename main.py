#!venv/bin/python
import asyncio
import sys
import logging.handlers
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode, BotCommand, BotCommandScope, BotCommandScopeChat
from aiogram.utils import exceptions
from tortoise import Tortoise

import filters
import handlers
import middleware
from handlers.admin import register_handlers_admin
from handlers.common import register_handlers_common
from handlers.workers import register_handlers_workers
from models import Worker
from utils import logging
from utils.config import config


async def init():
    await Tortoise.init(
        db_url='sqlite://main.db',
        modules={'models': ['models']})
    await Tortoise.generate_schemas()


async def on_startup(dispatcher: Dispatcher):
    bot = dispatcher.bot
    logging.setup()
    middleware.setup(dispatcher)
    filters.setup(dispatcher)
    handlers.setup(dispatcher)
    print((await bot.get_me()).username)
    await init()
    await set_commands(bot)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description='Start'),
    ]
    worker_commands = [
        BotCommand(command="/start", description='Start'),
        BotCommand(command="/workmenu", description='WorkerMenu'),
    ]
    admin_commands = worker_commands + [
        BotCommand(command='/blockuser', description='Заблокировать юзера'),
        BotCommand(command='/unblockuser', description='Разблокировать юзера'),
        BotCommand(command='/addworker', description='Добавить воркера'),
        BotCommand(command='/delworker', description='Удалить воркера'),
    ]
    ultra_admin_commands = admin_commands + [
        BotCommand(command='/addadmin', description='Добавить админа'),
        BotCommand(command='/deladmin', description='Удалить админа'),
    ]
    workers = Worker.all()
    tasks = list()
    async for worker in workers:
        try:
            scope = BotCommandScopeChat(worker.id)
            tasks.append(asyncio.ensure_future(bot.set_my_commands(admin_commands if worker.roleflag else worker_commands, scope)))
        except (exceptions.BotBlocked, exceptions.ChatNotFound, exceptions.UserDeactivated):
            pass
    await asyncio.gather(*tasks, return_exceptions=True)
    scope = BotCommandScopeChat(config.tg.admin_id)
    await bot.set_my_commands(commands)
    try:
        await bot.set_my_commands(ultra_admin_commands, scope)
    except (exceptions.BotBlocked, exceptions.ChatNotFound, exceptions.UserDeactivated):
        pass



async def on_shutdown(dispatcher: Dispatcher):
    await Tortoise.close_connections()


def main():
    bot = Bot(token=config.tg.token, parse_mode=ParseMode.HTML)
    dp = Dispatcher(bot, storage=MemoryStorage())
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)


if __name__ == '__main__':
    main()
