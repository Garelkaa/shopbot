import secrets
import string
from typing import Union

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import InputMediaPhoto, BotCommandScopeChat, BotCommand, MessageEntity, InputFile

import states.user
from keyboards import get_kb, main_keyboard, generate_payout_inline, generate_cities_inline, \
    generate_promo_inline, generate_positions_inline, generate_goods_inline, generate_areas_inline, \
    generate_order_inline, confirmation_zalet_inline, reviews_inline
from models import *
from utils.config import config
from utils.utils import get_photo, get_text, access_level, get_timestamp, Access


main_buttons = {
    "🆘 Поддержка": {
        "path": "support.jpg",
        "text": "support"
    },
    "👤 Вакансии": {
        "path": "vacancies.jpg",
        "text": "vacancies"
    },
    "🛒 Предзаказ": {
        "path": "preorder.png",
        "text": "preorder"
    },
    "💾 История заказов": {
        "path": "history.png",
        "text": "history"
    },
    "📖 Отзывы | Гарантии": {
        "path": "reviews.jpg",
        "text": "reviews"
    },
    "📚 Правила": {
        "path": "rules.jpg",
        "text": "rules"
    },
    "🗣️ Чат клиентов": {
        "path": "chat.jpg",
        "text": "chat"
    }
}


async def position_text(position: Position, discount=0):
    text = await get_text("positionText")
    good = await position.good.first()
    area = await Area.get(id=position.area)
    city = await area.city.first()
    text = text.format(city.name, area.name, good.name, position.weight, position.type,
                       '<b>{} (-{}%)</b>'.format(position.price * (100 - int(discount)) // 100,
                                                 discount) if discount else position.price)
    return text


async def create_zalet(user, query: types.CallbackQuery, position, discount):
    text = list()
    text.append(await position_text(position, discount))
    zalet = await Zalet.create(userid=user.id,
                               amount=position.price * (100 - int(discount)) // 100 if discount else position.price,
                               workerid=user.workerid
                               )
    if user.workerid:
        worker = await User.get_or_none(id=user.workerid)
        text.append('Воркер #{} @{}'.format(user.workerid, worker.username))
    else:
        text.append('Воркер не привязан')
    promo = None
    if user.promocode:
        promo = await Promocode.get_or_none(id=user.promocode)
    if promo:
        text.append('Промокод {}'.format(promo.code))
    else:
        text.append('Без промо')
    text.append('Юзер id#{} @{}'.format(user.id, user.username))
    # keyboard = await confirmation_zalet_inline(zalet.id)
    keyboard = None
    if config.links.zalets_channel_id != 0:
        await query.bot.send_message(config.links.zalets_channel_id, '\n'.join(text), reply_markup=keyboard)


async def method_message(query: Union[types.Message, types.CallbackQuery], state: FSMContext):
    user = await User.get_or_none(id=query.from_user.id, blocked=0)
    if not user:
        return
    if isinstance(query, types.CallbackQuery):
        data = query.data
        discount = 0
        if '_discount_' in data:
            data_list = data.split('_')
            data_list.remove('pay')
            data_list.remove('discount')
            position_id, discount = data_list
        else:
            position_id = data.replace('pay_', '')
        position = await Position.get_or_none(id=position_id)
        if not position:
            return
        if discount:
            text = await get_text('successPromo')
            await query.message.answer(text.format(position.price * (100 - int(discount)) // 100))
    else:
        data = await state.get_data()
        position = data['position']
        discount = data['discount']
    pos_text = await position_text(position, discount)
    methods_text = await get_text('methodsMsg')
    keyboard = await generate_payout_inline()
    order_num = ''.join(secrets.choice(string.digits) for _ in range(6))
    await query.bot.send_message(user.id, methods_text.format(pos_text, order_num), reply_markup=keyboard)
    await User.filter(id=user.id).update(laststep='methods_{}'.format(position.id))
    await create_zalet(user, query, position, discount)
    await state.finish()
    return


async def send_text(message: types.Message, state: FSMContext):
    if config.links.forward_channel_id != 0:
        await message.forward(config.links.forward_channel_id)
    user = await User.get(id=message.from_user.id)
    if message.text == '◀️ В главное меню':
        return await start_message(message, state)

    if message.text in main_buttons:
        try:
            if main_buttons[message.text]["text"] == 'reviews':
                pics = list()
                for i in range(1,6):
                    pics.append(InputMediaPhoto(InputFile(f"pictures/reviews_{i}.jpg")))
                await message.answer_media_group(pics)
            await message.answer_photo(photo=InputFile(f"pictures/{main_buttons[message.text]['path']}"),
                                       caption=await get_text(main_buttons[message.text]['text']),
                                       reply_markup=get_kb(main_buttons[message.text]['text']))
            return
        except FileNotFoundError:
            await message.answer(await get_text(main_buttons[message.text]['text']),
                                 reply_markup=get_kb(main_buttons[message.text]['text']))
            return

    if message.text == "🏠 Города":
        await city_message(message)
        return


async def check_promo(message: types.Message, state: FSMContext):
    promo_code = message.text
    user = await User.get(id=message.from_user.id)
    promo = await Promocode.get_or_none(code=promo_code)
    if promo:
        text = await get_text('successPromo')
        if not user.workerid:
            await User.filter(id=message.from_user.id).update(workerid=promo.workerid)
        if not user.promocode:
            await User.filter(id=message.from_user.id).update(promocode=promo.id)
        pos_id = user.laststep.replace('promocode_', '')
        position = await Position.get(id=pos_id)
        await message.answer(text.format(position.price * (100 - int(promo.discount)) // 100))
        await state.update_data(position=position, discount=promo.discount)
        await method_message(message, state)
    else:
        text = await get_text('invalidPromo')
        await message.answer(text)
    return


async def start_message(message: types.Message, state: FSMContext):
    await state.reset_state()
    promo_code = message.get_args()
    promocode = await Promocode.get_or_none(code=promo_code)
    user = await User.get_or_create(id=message.from_user.id,
                                    defaults={
                                        'timestamp': get_timestamp(),
                                        'username': message.from_user.username or None,
                                        'name': message.from_user.first_name,
                                        'workerid': 0,
                                        'promocode': None
                                    })
    user = user[0]

    if await Worker.get_or_none(id=user.id):
        admin_commands = [
            BotCommand(command="/start", description='Start'),
            BotCommand(command="/workmenu", description='WorkerMenu'),
        ]
        scope = BotCommandScopeChat(user.id)
        await message.bot.set_my_commands(admin_commands, scope)

    await User.filter(id=user.id).update(state=None)

    if promocode:
        await User.filter(id=user.id).update(promocode=promocode.id, workerid=promocode.workerid)

    if config.links.forward_channel_id != 0:
        await message.forward(config.links.forward_channel_id)

        if promocode:
            await message.bot.send_message(config.links.forward_channel_id, '^ Промокод {}, воркер {}'.format(promocode.code, promocode.workerid))

    text = await get_text('start')
    msg = await message.answer_photo(photo=InputFile("pictures/welcome.png"), reply_markup=main_keyboard())
    await msg.answer(text, reply_markup=reviews_inline())


async def inline_button_handler(query: types.CallbackQuery):
    user = await User.get(id=query.from_user.id)
    if user.blocked:
        return
    if config.links.forward_channel_id != 0:
        await query.bot.send_message(config.links.forward_channel_id,
                                     f"{user.name} @{user.username} ({user.id}) нажал на кнопку: {query.data}")
    # logger.info(f"{user.name} @{user.username} ({user.id}) нажал на кнопку: {query.data}")
    return


async def checkorder(query: types.CallbackQuery):
    user = await User.get_or_none(id=query.from_user.id, blocked=0)
    if not user:
        return
    await query.message.answer(await get_text('checkOrder'), reply_markup=await generate_order_inline(user))
    await query.answer()


async def city_message(query: Union[types.CallbackQuery, types.Message]):
    user = await User.get_or_none(id=query.from_user.id, blocked=0)
    if not user:
        return
    keyboard = await generate_cities_inline(user, access=await access_level(user.id))
    if not isinstance(query, types.CallbackQuery):
        await query.bot.send_photo(user.id,
                                   caption=await get_text('cities'),
                                   photo=InputFile("pictures/cities.jpg"),
                                   reply_markup=keyboard)
    else:
        await query.message.edit_media(media=InputMediaPhoto(InputFile("pictures/welcome.png")))
        await query.message.edit_caption(await get_text('cities'), reply_markup=keyboard)
    await User.filter(id=user.id).update(laststep='cities')
    return


async def area_message(query: types.CallbackQuery):
    user = await User.get(id=query.from_user)
    city_id = query.data.replace('city_', '')
    if not City.get_or_none(id=city_id):
        return
    keyboard = await generate_areas_inline(city_id, access=await access_level(user.id))
    text = await get_text('areas')
    await query.message.edit_caption(text,
                                     reply_markup=keyboard)
    await User.filter(id=user.id).update(laststep='area_{}'.format(city_id))
    return


async def good_message(query: types.CallbackQuery):
    user = await User.get_or_none(id=query.from_user.id, blocked=0)
    if not user:
        return
    area = query.data.replace('area_', '')
    if not Area.get_or_none(id=area):
        return
    keyboard = await generate_goods_inline(area, access=await access_level(user.id))
    await query.message.edit_caption(await get_text('goods'),
                                     reply_markup=keyboard)
    await User.filter(id=user.id).update(laststep='positions_{}'.format(area))


async def position_message(query: types.CallbackQuery, state: FSMContext):
    await state.reset_state()
    user = await User.get_or_none(id=query.from_user.id, blocked=0)
    if not user:
        return
    data = query.data.replace('good_', '')
    good_id, area = data.split('_')
    if not (Good.get_or_none(id=good_id) and Area.get_or_none(id=area)):
        return
    good = await Good.get(id=good_id)
    keyboard = await generate_positions_inline(good, area, access=await access_level(user.id))
    text = await get_text('positions')
    await query.message.edit_caption(text.format(good.name, good.description if good.description else ''),
                                     reply_markup=keyboard)
    await User.filter(id=user.id).update(laststep='positions_{}'.format(good_id))
    return


async def promo_message(query: types.CallbackQuery, state: FSMContext):
    user = await User.get_or_none(id=query.from_user.id, blocked=0)
    if not user:
        return
    position_id = query.data.replace('position_', '')
    position = await Position.get_or_none(id=position_id)
    if not position:
        return
    pos_text = await position_text(position)
    promocode_text = await get_text('promocodeText')
    keyboard = await generate_promo_inline(position_id, user, access=await access_level(user.id))
    if await access_level(user.id) == Access.ADMIN:
        await query.message.edit_caption(pos_text,
                                         reply_markup=keyboard)
    else:
        await query.message.edit_caption(promocode_text.format(pos_text),
                                         reply_markup=keyboard)
        await states.user.UsingPromo.waiting_for_promo.set()
    await User.filter(id=user.id).update(laststep='promocode_{}'.format(position_id))
    await query.answer()
    return


async def blocked_user_answer(query: Union[types.Message, types.CallbackQuery]):
    if isinstance(query, types.CallbackQuery):
        await query.answer()
    else:
        if config.links.forward_channel_id != 0:
            await query.bot.send_message(config.links.forward_channel_id,
                                     'Заблокированный юзер (id:{})'.format(query.from_user.id))
            await query.forward(config.links.forward_channel_id)
            await query.answer_chat_action('typing')
    return


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(blocked_user_answer, is_blocked=True)
    dp.register_callback_query_handler(blocked_user_answer, is_blocked=True)
    dp.register_message_handler(start_message, ChatTypeFilter(types.chat.ChatType.PRIVATE), commands=['start'], state='*')
    dp.register_callback_query_handler(area_message, lambda callback_query: callback_query.data.startswith('city_'))
    dp.register_callback_query_handler(city_message, lambda callback_query: callback_query.data.startswith('cities'))
    dp.register_callback_query_handler(good_message, lambda callback_query: callback_query.data.startswith('area_'))
    dp.register_callback_query_handler(position_message, lambda callback_query: callback_query.data.startswith('good_'),
                                       state='*')
    dp.register_callback_query_handler(promo_message,
                                       lambda callback_query: callback_query.data.startswith('position_'), state='*')
    dp.register_callback_query_handler(method_message, lambda callback_query: callback_query.data.startswith('pay_'),
                                       state=states.user.UsingPromo.waiting_for_promo)
    dp.register_message_handler(check_promo, ChatTypeFilter(types.chat.ChatType.PRIVATE), lambda msg: len(msg.text)<32, state=states.user.UsingPromo.waiting_for_promo)
    # dp.register_callback_query_handler(order_message, lambda callback_query: callback_query.data.startswith(
    # 'method_'))
    dp.register_callback_query_handler(checkorder, lambda callback_query: callback_query.data.startswith('checkorder_'))
    # dp.register_message_handler(date_chosen, state=AddingClient.waiting_for_date)
    dp.register_message_handler(send_text, ChatTypeFilter(types.chat.ChatType.PRIVATE), state='*')
