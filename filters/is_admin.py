from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from utils.utils import Access, access_level


class AdminFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def check(self, message: types.Message):
        return await access_level(message.from_user.id) == Access.ADMIN
