from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from utils.utils import Access, access_level


class WorkerFilter(BoundFilter):
    key = 'is_worker'

    def __init__(self, is_worker):
        self.is_worker = is_worker

    async def check(self, message: types.Message):
        return await access_level(message.from_user.id) in [Access.ADMIN, Access.WORKER]
