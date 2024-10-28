from aiogram import Dispatcher
from aiogram.dispatcher.filters import MediaGroupFilter

from .is_admin import AdminFilter
from .is_worker import WorkerFilter
from .is_blocked import BlockedFilter


def setup(dp: Dispatcher):
    dp.filters_factory.bind(AdminFilter)
    dp.filters_factory.bind(WorkerFilter)
    dp.filters_factory.bind(BlockedFilter)
    dp.filters_factory.bind(MediaGroupFilter)
