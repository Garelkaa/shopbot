from aiogram import Dispatcher

from .admin import register_handlers_admin
from .common import register_handlers_common
from .workers import register_handlers_workers


def setup(dp: Dispatcher):
    register_handlers_admin(dp)
    register_handlers_workers(dp)
    register_handlers_common(dp)