import datetime
from enum import Enum

from aiogram import Bot
from aiogram.dispatcher.filters.state import State, StatesGroup

from models import Picture, Texts, Worker
from utils.config import config


class Access(Enum):
    USER = 0
    WORKER = 1
    ADMIN = 2


class CreateGood(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_photo = State()


class CreatePosition(StatesGroup):
    waiting_for_good = State()
    waiting_for_price = State()
    waiting_for_weight = State()


class CreateArea(StatesGroup):
    waiting_for_area = State()


class CreateCity(StatesGroup):
    waiting_for_city = State()


class OrderPromo(StatesGroup):
    waiting_for_promo = State()


def get_timestamp():
    return int(datetime.datetime.utcnow().timestamp())


async def get_text(name):
    text = await Texts.get(pk=name)
    return text.value


async def get_photo(picname: str, bot: Bot):
    pic = await Picture.get_or_none(pk=picname) or open("pictures/" + picname, 'rb')
    if type(pic) == Picture:
        pass
    else:
        sent = await bot.send_photo(config.links.forward_channel_id, pic, disable_notification=True)
        await Picture.create(name=picname, id=sent.photo[-1].file_id)
        await sent.delete()
        # await bot.delete_message(config.links.forward_channel_id, sent.message_id)
        pic = await Picture.get(pk=picname)
    return pic.id


async def access_level(user_id: int):
    worker = await Worker.get_or_none(id=user_id)
    if not worker and user_id != config.tg.admin_id:
        return Access.USER
    if user_id == config.tg.admin_id or worker.roleflag == 1:
        return Access.ADMIN
    return Access.WORKER
