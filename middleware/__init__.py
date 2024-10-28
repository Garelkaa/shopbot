from aiogram import Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from .album import AlbumMiddleware
from .throttling import ThrottlingMiddleware


def setup(dp: Dispatcher):
    dp.middleware.setup(AlbumMiddleware())
    dp.middleware.setup(LoggingMiddleware())
    dp.middleware.setup(ThrottlingMiddleware())

