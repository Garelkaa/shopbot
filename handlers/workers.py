import asyncio
import secrets
import string
from typing import Union, List

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text, Command, MediaGroupFilter, ChatTypeFilter
from aiogram.types import ContentType
from aiogram.utils import exceptions

from keyboards import generate_promo_cities_inline, generate_worker_promos_inline, generate_promo_edit_inline, \
    worker_keyboard, worker_stats_inline
from models import *
from utils.config import config
#
from utils.utils import get_text


# async def mass_send(query: types.Message, album: List[types.Message] = None):
async def mass_send(query: types.Message):
    worker = await Worker.get_or_none(id=query.from_user.id)
    if not worker and not query.from_user.id == config.tg.admin_id:
        return
    media = types.MediaGroup()
    if config.tg.admin_id == query.from_user.id or worker.roleflag == 1:
        users = User.all()
    else:
        users = User.filter(workerid=worker.id)
    users_to_delete = list()
    photo = None
    video = None
    text = query.get_args()
    if query.photo:
        photo = query.photo[-1].file_id
    elif query.video:
        video = query.video.file_id
    async for user in users:
        try:
            if photo:
                await query.bot.send_photo(user.id, photo, caption=query.get_args())
            elif video:
                await query.bot.send_video(user.id, video, caption=query.get_args())
            else:
                await query.bot.send_message(user.id, query.get_args())
        except (exceptions.BotBlocked, exceptions.ChatNotFound, exceptions.UserDeactivated):
            users_to_delete.append(asyncio.ensure_future(User.filter(id=user.id).delete()))
    deleted = await asyncio.gather(*users_to_delete)
    await query.answer('Рассылка окончена, юзеров удалено: {}'.format(len(users_to_delete)))


async def worker_stats_menu(query: types.CallbackQuery):
    worker = await Worker.get(id=query.from_user)
    text = '🦣 Пришло юзеров {}\n 🟢 Подтвержденных залётов: {}'
    mammoths = await User.filter(workerid=worker.id).count()
    zalets = await Zalet.filter(workerid=worker.id, accepted=1).count()
    keyboard = worker_stats_inline()
    await query.message.edit_text(text.format(mammoths, zalets), reply_markup=keyboard)


async def worker_menu(query: Union[types.CallbackQuery, types.Message]):
    keyboard = worker_keyboard()
    user = await User.get(id=query.from_user.id)
    text = await get_text('workMenu')
    if isinstance(query, types.CallbackQuery):
        await query.message.edit_text(text.format(user.username), reply_markup=keyboard)
    else:
        await query.answer(text.format(user.username), reply_markup=keyboard)
    return


async def promos_worker_menu(query: types.CallbackQuery):
    user = await User.get(id=query.from_user.id)
    text = await get_text("promocodeMenu")
    keyboard = await generate_worker_promos_inline(user.id)
    await query.message.edit_text(text, reply_markup=keyboard)
    await User.filter(id=query.from_user.id).update(state=None)


async def promo_edit_menu(query: types.CallbackQuery, promo_id=None):
    # user = await User.get(id=query.from_user.id)
    data = query.data
    if not promo_id:
        promo_id = data.split('_')[-1]
    promocode = await Promocode.get(id=promo_id)
    text = await get_text("promocodeEdit")
    keyboard = await generate_promo_edit_inline(promo_id)
    me = await query.bot.get_me()
    link = 'http://t.me/{}?start={}'.format(me.username, promocode.code)
    mammoths = await User.filter(promocode=promo_id).count()
    await query.message.edit_text(text.format(promocode.code, link, promocode.discount, mammoths),
                                     reply_markup=keyboard)
    return


async def generate_new_promo(query: types.CallbackQuery):
    user = await User.get(id=query.from_user.id)
    letters = string.ascii_uppercase
    code = ''.join(secrets.choice(letters) for _ in range(6))
    promocode = await Promocode.create(code=code, workerid=user.id)
    await query.answer('Промокод {} создан'.format(code))
    await promos_worker_menu(query)
    return


async def edit_promo(query: types.CallbackQuery):
    data = query.data
    if 'remove_promo_' in data:
        promo_id = data.replace('remove_promo_', '')
        await Promocode.filter(id=promo_id).delete()
        await User.filter(promocode=promo_id).update(promocode=None)
        await query.answer('Промокод удален')
        await promos_worker_menu(query)
    elif 'set_promo_discount_' in data:
        promo_id, discount = data.replace('set_promo_discount_', '').split('_')
        await Promocode.filter(id=promo_id).update(discount=discount)
        await query.answer('Скидка изменена на {}%'.format(discount))
        await promo_edit_menu(query, promo_id=promo_id)
        return


async def promo_cities_menu(query: types.CallbackQuery, promo_id=None):
    data = query.data
    if not promo_id:
        promo_id = data.split('_')[-1]
    keyboard = await generate_promo_cities_inline(promo_id)
    text = await get_text('promocodeCities')
    await query.message.edit_text(text, reply_markup=keyboard)
    return


async def change_promo_cities(query):
    data = query.data
    promo_id, city_id = data.split('_')[-2:]
    promocode = await Promocode.get(id=promo_id)
    cities_id = [int(x) for x in promocode.cities.strip('|').split('|')] if promocode.cities else list()
    if 'promo_add_city_' in data:
        cities_id.append(int(city_id))
    else:
        cities_id.remove(int(city_id))
    cities_str = '|'.join([str(x) for x in cities_id])
    await Promocode.filter(id=promo_id).update(cities=cities_str)
    await promo_cities_menu(query, promo_id=promo_id)
    return


def register_handlers_workers(dp: Dispatcher):
    dp.register_message_handler(worker_menu, ChatTypeFilter(types.chat.ChatType.PRIVATE), is_worker=True, commands=['workmenu'], state='*')
    # dp.register_message_handler(mass_send, is_media_group=True,
    #                             content_types=[ContentType.TEXT, ContentType.PHOTO], state='*')
    # dp.register_message_handler(mass_send, ChatTypeFilter(types.chat.ChatType.PRIVATE), MediaGroupFilter(True), is_worker=True,
    #                             content_types=[ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO], state='*')
    dp.register_message_handler(mass_send, MediaGroupFilter(False), Command('mass_send', ignore_caption=False),
                                content_types=[ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO], state='*')
    # dp.register_message_handler(aaa, content_types=[ContentType.TEXT, ContentType.PHOTO], state='*')
    dp.register_callback_query_handler(promos_worker_menu, lambda callback_query: callback_query.data.startswith(
        'promos_menu'), is_worker=True)
    dp.register_callback_query_handler(generate_new_promo, lambda callback_query: callback_query.data.startswith(
        'generate_promo'), is_worker=True)
    dp.register_callback_query_handler(promo_edit_menu, lambda callback_query: callback_query.data.startswith(
        'edit_promo_'), is_worker=True)
    dp.register_callback_query_handler(promo_cities_menu, lambda callback_query: callback_query.data.startswith(
        'choose_cities_promo_'), is_worker=True)
    dp.register_callback_query_handler(edit_promo, lambda callback_query: callback_query.data.startswith(
        'set_promo_discount_') or callback_query.data.startswith('remove_promo_'), is_worker=True)
    dp.register_callback_query_handler(change_promo_cities, lambda callback_query: callback_query.data.startswith(
        'promo_add_city_') or callback_query.data.startswith('promo_remove_city_'), is_worker=True)
    dp.register_callback_query_handler(worker_menu, lambda callback_query: callback_query.data.startswith(
        'worker_menu'), is_worker=True)
    dp.register_callback_query_handler(worker_stats_menu, lambda callback_query: callback_query.data.startswith(
        'stats_menu'), is_worker=True)
    # dp.register_message_handler(start_cmd, commands=['start'], state='*')
    # dp.register_message_handler(save_cmd, commands=['save_file'], state='*')
    # dp.register_message_handler(date_chosen, state=AddingClient.waiting_for_date)