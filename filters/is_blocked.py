from typing import Union

from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from models import User


class BlockedFilter(BoundFilter):
    key = 'is_blocked'

    def __init__(self, is_blocked):
        self.is_blocked = is_blocked

    async def check(self, query: Union[types.Message, types.CallbackQuery]):
        user = await User.get_or_none(id=query.from_user.id)
        return user and user.blocked
