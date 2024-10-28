import asyncio
import math
from typing import Union

import aiogram
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text, IDFilter, ChatTypeFilter
import aiogram.utils.markdown as fmt

from aiogram.types import ReplyKeyboardRemove, ContentType, BotCommand, BotCommandScopeChat
from aiogram.utils import exceptions

import states
from handlers.common import city_message, area_message
from keyboards import generate_good_edit_inline, admin_keyboard, generate_goods_admin_inline, confirmation_zalet_inline, \
    generate_areas_inline, generate_goods_inline, generate_promo_inline, generate_positions_inline, \
    generate_cities_inline, admin_stats_inline, method_pay_inline, generate_workers_list_inline, \
    generate_links_menu_inline
from models import Good, Promocode, User, Area, Zalet, Position, City, Picture, Worker, Texts
from utils.config import config, write_config
from utils.utils import get_text, get_timestamp, access_level, Access, get_photo


async def position_text(position, discount=0):
    text = await get_text("positionText")
    good = await position.good.first()
    area = await Area.get(id=position.area)
    city = await area.city.first()
    text = text.format(city.name, area.name, good.name, position.weight, position.type,
                       '<b>{} (-{}%)</b>'.format(position.price * (100 - int(discount)) // 100,
                                                 discount) if discount else position.price)
    return text


#  '👷 Воркеры'
async def workers_list_menu(query: types.Message | types.CallbackQuery, state: FSMContext):
    workers_count = await Worker.all().count()
    if workers_count == 0:
        await query.answer('Нет воркеров')
        return
    if workers_count < 10:
        workers = await Worker.all().order_by('id')
        keyboard = None
    elif isinstance(query, types.Message):
        page = 1
        total_pages = math.ceil(workers_count/10.0)
        workers = await Worker.all().order_by('id').limit(10)
        keyboard = await generate_workers_list_inline(1, total_pages)
    else:
        page = int(query.data.replace('workers_list_', ''))
        total_pages = math.ceil(workers_count / 10.0)
        offset = (page - 1) * 10
        workers = await Worker.all().order_by('id').offset(offset).limit(10)
        keyboard = await generate_workers_list_inline(page, total_pages)
    text = list()
    for worker in workers:
        worker_user = await User.get_or_none(id=worker.id)
        worker_text = list()
        if worker_user and worker_user.username:
            worker_text.append('{} @{}{}'.format(fmt.hbold(fmt.quote_html(worker_user.name)),
                                                 worker_user.username,
                                                 fmt.hbold(' (Админ)') if worker.roleflag==1 else ''))
        elif worker_user:
            worker_text.append('{}'.format(fmt.hbold(fmt.quote_html(worker_user.name))))
        worker_text.append(f'<a href="tg://user?id={worker.id}">{worker.id}</a>')
        worker_text.append(f'Удалить: /delworker{worker.id}')
        text.append('\n'.join(worker_text))
    if isinstance(query, types.CallbackQuery):
        try:
            await query.message.edit_text('\n\n'.join(text), reply_markup=keyboard)
        except aiogram.utils.exceptions.MessageNotModified:
            await query.answer('¯\_(ツ)_/¯')
    else:
        await query.answer('\n\n'.join(text), reply_markup=keyboard)


async def method_pay_edit_menu(message: types.Message, state: FSMContext):
    await state.reset_state()
    text = await get_text('methodsMsg')
    keyboard = await method_pay_inline()
    await message.answer('Текущий текст оплаты:')
    await message.answer(text, reply_markup=keyboard)


async def links_edit_menu(message: types.Message, state: FSMContext):
    await state.reset_state()
    keyboard = await generate_links_menu_inline()
    text = list()
    text.append('Юзернейм админа (для предзаказов и связи по вакансиям): ')
    text.append(f'@{config.links.admin_username}\n')
    text.append('Юзернейм оператора (для связи по оплате): ')
    text.append(f'@{config.links.support_username}\n')
    text.append('ID канала (или группы) для отстука (0 - отключить отстук): ')
    text.append(f'{config.links.forward_channel_id}\n')
    text.append('ID канала (или группы) для залётов (0 - отключить залёты): ')
    text.append(f'{config.links.zalets_channel_id}\n')
    text.append('Ссылка на канал с отзывами: ')
    text.append(f'{config.links.reviews_channel_url}\n')
    await message.answer(' '.join(text), reply_markup=keyboard)

async def edit_link_chosen(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    await states.admin.ChangingLink.waiting_for_link.set()
    link_type = query.data.replace('link_change_', '')
    await state.set_data({'link': link_type})
    if link_type == 'reviews_channel_url':
        await query.message.answer('Введи ссылку')
    elif link_type in ['admin_username', 'operator_username']:
        await query.message.answer('Введи юзернейм')
    else:
        await query.message.answer('Введи ID')


async def edit_link_text_received(message: types.Message, state: FSMContext):
    data = await state.get_data()
    link_type = data['link']
    if link_type == 'reviews_channel_url':
        if message.text.startswith('https://t.me/'):
            config.links.reviews_channel_url = message.text
        else:
            await message.answer('Какая-то неправильная ссылка, попробуй снова')
            return
    elif link_type in ['admin_username', 'operator_username']:
        username = message.text.replace('@','')
        if link_type == 'admin_username':
            config.links.admin_username = username
        else:
            config.links.support_username = username
    else:
        if message.text == '0':
            if link_type == 'forward_channel_id':
                config.links.forward_channel_id = 0
            else:
                config.links.zalets_channel_id = 0
        else:
            try:
                await message.bot.get_chat(message.text)
            except aiogram.exceptions.ChatNotFound:
                await message.answer('Чат не найден. Возможно, бот не добавлен в чат?\nПопробуй снова')
                return
            finally:
                if link_type == 'forward_channel_id':
                    config.links.forward_channel_id = int(message.text)
                else:
                    config.links.zalets_channel_id = int(message.text)
    write_config(config)
    await state.finish()
    await message.answer('Готово')
    await links_edit_menu(message, state)


async def change_method_text(query: types.CallbackQuery, state: FSMContext):
    await query.message.answer('Введите новый текст: ({0} - текст позиции, {1} - номер заказа)')
    await states.admin.ChangingMethodText.waiting_for_text.set()


async def new_method_pay_received(message: types.Message, state: FSMContext):
    if '{0}' in message.text and '{1}' in message.text:
        await Texts.filter(pk='methodsMsg').update(value=message.html_text)
        await state.finish()
        await message.answer('Текст обновлён')
    else:
        await message.answer('В тексте отсутствует {0} или {1}, попробуйте снова')


# '🎟️ Промокоды'
async def promos_admin_menu(message: types.Message, state: FSMContext):
    await message.answer('ну тут промокоды будут')


# '📊 Статистика'
async def stats_menu(message: types.Message, state: FSMContext):
    await state.reset_state()
    users = await User.all().count()
    mammoths = await User.filter(workerid__not=0).count()
    text = 'Юзеров всего {}\nПривязано к воркерам {}'
    keyboard = await admin_stats_inline()
    await message.answer(text.format(users, mammoths), reply_markup=keyboard)


async def clear_users(query: types.CallbackQuery):
    users = User.all()
    worker_ids = [x.id for x in await Worker.all()]
    users_count = await users.count()
    bot_blocked_count = 0
    deactivated_users_count = 0
    chat_not_found = 0
    users_to_delete = list()
    num = 0
    percentage = 0
    await query.answer()
    msg = await query.message.answer('Начинаем очистку...')
    async for user in users:
        if user.id not in worker_ids:
            try:
                await query.bot.send_chat_action(user.id, types.chat.ChatActions.TYPING)
            except exceptions.BotBlocked:
                bot_blocked_count += 1
                users_to_delete.append(asyncio.ensure_future(User.filter(id=user.id).delete()))
            except exceptions.ChatNotFound:
                chat_not_found += 1
                users_to_delete.append(asyncio.ensure_future(User.filter(id=user.id).delete()))
            except exceptions.UserDeactivated:
                deactivated_users_count += 1
                users_to_delete.append(asyncio.ensure_future(User.filter(id=user.id).delete()))
        num += 1
        new_percentage = num * 100 // users_count
        if new_percentage > percentage:
            await msg.edit_text('{}{} {}%\n'
                                'Бот заблочен: {}\n'
                                'Удалённых аккаунтов: {}\n'
                                'Не найдено чатов: {}'.format('▰' * (new_percentage // 5),
                                                              '▱' * (20 - new_percentage // 5),
                                                              new_percentage,
                                                              bot_blocked_count,
                                                              deactivated_users_count,
                                                              chat_not_found
                                                              ))
            percentage = new_percentage
    deleted = await asyncio.gather(*users_to_delete)
    await msg.edit_text('Всего удалено юзеров: {}\n'
                        'Бот заблочен: {}\n'
                        'Удалённых аккаунтов: {}\n'
                        'Не найдено чатов: {}'.format(len(deleted),
                                                      bot_blocked_count,
                                                      deactivated_users_count,
                                                      chat_not_found))


# '📦 Товары'
async def goods_menu(query: Union[types.Message, types.CallbackQuery], state: FSMContext):
    await state.reset_state()
    keyboard = await generate_goods_admin_inline()
    text = await get_text('goods')
    if isinstance(query, types.CallbackQuery):
        await query.message.edit_text(text, reply_markup=keyboard)
    else:
        await query.answer(text, reply_markup=keyboard)
    await User.filter(id=query.from_user.id).update(state=None)


# '/start'
async def admin_menu(message: types.Message, state: FSMContext):
    await state.reset_state()
    admin_commands = [
        BotCommand(command="/start", description='Start'),
        BotCommand(command="/workmenu", description='WorkerMenu'),
    ]
    scope = BotCommandScopeChat(message.from_user.id)
    await message.bot.set_my_commands(admin_commands, scope)

    keyboard = admin_keyboard()
    user = await User.get_or_create(id=message.from_user.id,
                                    defaults={
                                        'timestamp': get_timestamp(),
                                        'username': message.from_user.username or None,
                                        'name': message.from_user.first_name
                                    })
    user = user[0]
    await User.filter(id=user.id).update(state=None)
    text = await get_text('workMenu')
    await message.answer(text.format(user.username), reply_markup=keyboard)


async def city_edit(query: types.CallbackQuery):
    user = await User.get(id=query.from_user.id)
    data = query.data
    if data.startswith('add_city'):
        await query.message.answer('Введи название')
        await states.admin.AddingCity.waiting_for_name.set()
        await query.answer()
        return
    city_id = data.split('_')[-1]
    if data.startswith('remove_city'):
        city = await City.get(id=city_id)
        areas = Area.filter(city=city)
        async for area in areas:
            await Position.filter(area=area.id).delete()
            await Area.filter(id=area.id).delete()
        await City.filter(id=city_id).delete()
        await query.answer('Город удален')
        await city_message(query)
    elif data.startswith('unhide_city'):
        await City.filter(id=city_id).update(hidden=0)
        keyboard = await generate_areas_inline(city_id, access=await access_level(user.id))
        await query.answer('Город раскрыт')
        await query.message.edit_reply_markup(reply_markup=keyboard)
    elif data.startswith('hide_city'):
        await City.filter(id=city_id).update(hidden=1)
        keyboard = await generate_areas_inline(city_id, access=await access_level(user.id))
        await query.answer('Город скрыт')
        await query.message.edit_reply_markup(reply_markup=keyboard)


async def adding_city_name_entered(message: types.Message, state: FSMContext):
    await City.create(name=message.text)
    await message.answer('Готова')
    user = await User.get(id=message.from_user.id)
    keyboard = await generate_cities_inline(user, access=await access_level(user.id))
    await message.answer_photo(photo=await get_photo('cities.jpg', message.bot),
                               caption=await get_text('cities'),
                               reply_markup=keyboard)
    await state.finish()


async def area_edit(query: types.CallbackQuery, state: FSMContext):
    user = await User.get(id=query.from_user.id)
    data = query.data
    if data.startswith('add_area_'):
        await query.message.answer('Введи название')
        await states.admin.AddingArea.waiting_for_name.set()
        city_id = data.replace('add_area_', '')
        await state.update_data(city_id=city_id)
        await query.answer()
        return
    area_id = data.split('_')[-1]
    area = await Area.get(id=area_id)
    if data.startswith('remove_area'):
        await Area.filter(id=area_id).delete()
        await Position.filter(area=area_id).delete()
        await query.answer('Район удален')
        keyboard = await generate_areas_inline(await area.city, access=await access_level(user.id))
        await query.message.edit_caption(await get_text('areas'),
                                         reply_markup=keyboard)
        await User.filter(id=user.id).update(laststep='area_{}'.format(area.city))
    elif data.startswith('hide_area'):
        await Area.filter(id=area_id).update(hidden=1)
        await query.answer('Район скрыт')
        keyboard = await generate_goods_inline(area_id, access=await access_level(user.id))
        await query.message.edit_reply_markup(reply_markup=keyboard)
    elif data.startswith('unhide_area'):
        await Area.filter(id=area_id).update(hidden=0)
        await query.answer('Район раскрыт')
        keyboard = await generate_goods_inline(area_id, access=await access_level(user.id))
        await query.message.edit_reply_markup(reply_markup=keyboard)


async def adding_area_name_entered(message: types.Message, state: FSMContext):
    data = await state.get_data()
    city = await City.get(id=data['city_id'])
    await Area.create(name=message.text, city=city)
    await message.answer('Готова')
    keyboard = await generate_areas_inline(data['city_id'], access=await access_level(message.from_user.id))
    await message.answer_photo(photo=await get_photo('cities.jpg', message.bot),
                               caption=await get_text('areas'),
                               reply_markup=keyboard)
    await state.finish()


async def position_edit(query: types.CallbackQuery, state: FSMContext):
    user = await User.get(id=query.from_user.id)
    data = query.data
    if data.startswith('add_position_'):
        keyboard = await generate_goods_admin_inline()
        await query.message.answer('Выбери товар:', reply_markup=keyboard)
        await states.admin.AddingPosition.waiting_for_good.set()
        area_id = data.replace('add_position_', '')
        await state.update_data(area_id=area_id)
        await query.answer()
        return
    position_id = data.split('_')[-1]
    position = await Position.get(id=position_id)
    if data.startswith('remove_position'):
        await Position.filter(id=position_id).delete()
        await query.answer('Позиция удалена')
        keyboard = await generate_positions_inline(await position.good, position.area,
                                                   access=await access_level(user.id))
        await query.message.edit_caption(await get_text('goods'),
                                         reply_markup=keyboard)
        await User.filter(id=user.id).update(laststep='positions_{}'.format(position.area))
        return
    pos_text = await position_text(position)
    promocode_text = await get_text('promocodeText')
    if data.startswith('hide_position'):
        await Position.filter(id=position_id).update(hidden=1)
        keyboard = await generate_promo_inline(position_id, user, access=await access_level(user.id))
        await query.answer('Позиция скрыта')
        await query.message.edit_caption(pos_text,
                                         reply_markup=keyboard)
    elif data.startswith('unhide_position'):
        await Position.filter(id=position_id).update(hidden=0)
        keyboard = await generate_promo_inline(position_id, user, access=await access_level(user.id))
        await query.answer('Позиция раскрыта')
        await query.message.edit_caption(pos_text,
                                         reply_markup=keyboard)
    return


async def adding_position_good_chosen(query: types.CallbackQuery, state: FSMContext):
    good_id = query.data.replace('show_good_', '')
    await query.message.delete()
    await state.update_data(good_id=good_id)
    await query.message.answer('Введи вес')
    await states.admin.AddingPosition.next()


async def adding_position_weight_entered(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.answer('Введи тип')
    await states.admin.AddingPosition.next()


async def adding_position_type_entered(message: types.Message, state: FSMContext):
    await state.update_data(type=message.text)
    await message.answer('Введи цену')
    await states.admin.AddingPosition.next()


async def adding_position_price_entered(message: types.Message, state: FSMContext):
    try:
        await state.update_data(price=int(message.text))
    except ValueError:
        await message.answer('Цену только в цыфрах!!1')
        return
    data = await state.get_data()
    good = await Good.get(id=data['good_id'])
    await Position.create(area=data['area_id'], good=good, price=data['price'], weight=data['weight'],
                          type=data['type'])
    await message.answer('Готова')
    keyboard = await generate_goods_inline(data['area_id'], access=await access_level(message.from_user.id))
    await message.answer_photo(photo=await get_photo('cities.jpg', message.bot),
                               caption=await get_text('goods'),
                               reply_markup=keyboard)
    await state.finish()


async def edit_good(query: types.CallbackQuery):
    data = query.data
    if data.startswith('add_good'):
        await states.admin.AddingGood.waiting_for_name.set()
        await query.message.answer('Введи название товара:')
        await query.answer()
        return
    good_id = data.split('_')[-1]
    if data.startswith('remove_good'):
        await Good.filter(id=good_id).delete()
        await Picture.filter(name='good_{}.jpg'.format(good_id)).delete()
        await query.answer('Товар удален')
        await goods_menu(query)
        return
    if data.startswith('hide_good'):
        await Good.filter(id=good_id).update(hidden=1)
        await query.answer('Товар скрыт')
    elif data.startswith('unhide_good'):
        await Good.filter(id=good_id).update(hidden=0)
        await query.answer('Товар раскрыт')
    await show_good_menu(query)
    return


async def good_name_entered(message: types.Message, state: FSMContext):
    if await Good.get_or_none(name=message.text):
        await message.answer('Тааак, падажжи ёбана\nТакой товар уже есть')
        await state.finish()
        await goods_menu(message)
        return
    await state.update_data(name=message.text)
    await message.answer('Введи описание (/skip, если отсутствует)')
    await states.admin.AddingGood.next()


async def good_description_entered(message: types.Message, state: FSMContext):
    if message.text != '/skip':
        await state.update_data(description=message.text)
    await message.answer('Отправь фото товара (/skip, если отсутствует)')
    await states.admin.AddingGood.next()


async def good_photo_sent(message: types.Message, state: FSMContext):
    if message.photo:
        await state.update_data(photo=message.photo[-1].file_id)
    elif message.text != '/skip':
        await message.answer('Это не фото')
        return
    data = await state.get_data()
    good = await Good.create(name=data['name'])
    if 'description' in data:
        await Good.filter(name=data['name']).update(description=data['description'])
    if 'photo' in data:
        await Picture.update_or_create(name='good_{}.jpg'.format(good.id), id=data['photo'])
    await message.answer('Готова!')
    await state.finish()
    await goods_menu(message)


async def show_good_menu(query: types.CallbackQuery):
    data = query.data
    good_id = data.split('_')[-1]
    good = await Good.get(id=good_id)
    text = 'Название: {}\nОписание: {}'.format(good.name, good.description)
    keyboard = await generate_good_edit_inline(good_id)
    await query.message.edit_text(text, reply_markup=keyboard)
    return


async def confirm_zalet(query: types.CallbackQuery):
    data = query.data
    if data.startswith('accept_zalet_'):
        zalet_id = data.replace('accept_zalet_', '')
        await Zalet.filter(id=zalet_id).update(accepted=1)
        if config.links.zalets_channel_id:
            text = await get_text('acceptedZalet')
            zalet = await Zalet.get(id=zalet_id)
            worker = await User.get(id=zalet.workerid)
            await query.bot.send_message(config.links.zalets_channel_id,
                                         text.format(zalet.amount, worker.name, worker.username,
                                                     worker.id, '', ''))
            await query.answer('Принято!')
            await query.message.edit_reply_markup(reply_markup=None)
    elif data.startswith('decline_zalet_'):
        await query.message.delete()
    return


async def cancel_state(message: types.Message, state: FSMContext):
    await state.reset_state()
    await message.answer('Отменено')
    return


async def add_worker(message: types.Message, state: FSMContext):
    await state.reset_state()
    # args = message.get_args()
    try:
        args = int(message.text.replace('/addworker', '').strip())
    except ValueError:
        args = None
    if not args:
        await message.answer('Введи id\nНапример, /addworker 123123')
        return
    worker = await Worker.get_or_none(id=args)
    if worker:
        await message.answer('Воркер с id {} уже есть'.format(args))
        return
    worker = await Worker.create(id=args)
    await message.answer('Воркер с id {} добавлен'.format(worker.id))

async def add_admin(message: types.Message, state: FSMContext):
    await state.reset_state()
    if not message.from_user.id == config.tg.admin_id:
        return
    try:
        args = int(message.text.replace('/addadmin', '').strip())
    except ValueError:
        args = None
    if not args:
        await message.answer('Введи id\nНапример, /addadmin 123123')
        return
    worker = await Worker.get_or_none(id=args, roleflag=1)
    if worker:
        await message.answer('Админ с id {} уже есть'.format(args))
        return
    worker = await Worker.update_or_create(id=args, roleflag=1)[0]
    await message.answer('Админ с id {} добавлен'.format(worker.id))


async def remove_worker(message: types.Message, state: FSMContext):
    await state.reset_state()
    try:
        args = int(message.text.replace('/delworker', '').strip())
    except ValueError:
        args = None
    if not args:
        await message.answer('Введи id\nНапример /delworker 123123')
        return
    if int(args) == message.from_user.id:
        await message.answer('Зачем удалять самого себя?')
        return
    if int(args) == config.tg.admin_id:
        await message.answer('Не смей трогать верховного админа')
        return
    worker = await Worker.get_or_none(id=args)
    if not worker:
        await message.answer(f'Воркера с id {args} нет в базе')
    else:
        await Worker.filter(id=args).delete()
        await message.answer(f'Воркер с id {args} удален,\n чтобы вернуть, нажми /addworker{args}')


async def remove_admin(message: types.Message, state: FSMContext):
    await state.reset_state()
    if not message.from_user.id == config.tg.admin_id:
        return
    try:
        args = int(message.text.replace('/deladmin', '').strip())
    except ValueError:
        args = None
    if not args:
        await message.answer('Введи id\nНапример /deladmin 123123')
        return
    if int(args) == message.from_user.id:
        await message.answer('Зачем удалять самого себя?')
        return
    worker = await Worker.get_or_none(id=args)
    if not worker:
        await message.answer(f'Админа с id {args} нет')
    elif worker.roleflag == 0:
        await message.answer(f'У id {args} нет статуса админа')
    else:
        await Worker.filter(id=args, roleflag=1).update(roleflag=0)
        await message.answer(f'Админ с id {args} опущен до воркера,\n чтобы вернуть, нажми /addadmin{args}\nЧтобы удалить из воркеров, нажми /delworker{args}')


async def block_user(message: types.Message, state: FSMContext):
    await state.reset_state()
    try:
        args = int(message.text.replace('/blockuser', '').strip())
    except ValueError:
        args = None
    if not args:
        await message.answer('Введи id\nНапример /blockuser 123123')
        return
    if int(args) == message.from_user.id:
        await message.answer('Зачем блокировать самого себя?')
        return
    if int(args) == config.tg.admin_id:
        await message.answer('Не смей трогать верховного админа')
        return
    user = await User.get_or_create(id=int(args),
                             defaults={
                                        'timestamp': get_timestamp(),
                                        'username': None,
                                        'name': '',
                                        'workerid': 0,
                                        'promocode': None
                                    })[0]
    await User.filter(id=args).update(blocked=True)
    await Worker.filter(id=args).delete()
    await message.answer('Юзер {}с id {} заблокирован'.format(f'{user.username} ' if user.username else '', args))

async def unblock_user(message: types.Message, state: FSMContext):
    await state.reset_state()
    try:
        args = int(message.text.replace('/unblockuser', '').strip())
    except ValueError:
        args = None
    if not args:
        await message.answer('Введи id\nНапример /unblockuser 123123')
        return
    if int(args) == message.from_user.id:
        await message.answer('Не майся фигнёй')
        return
    if int(args) == config.tg.admin_id:
        await message.answer('Не смей трогать верховного админа')
        return
    user = await User.get_or_create(id=int(args),
                             defaults={
                                        'timestamp': get_timestamp(),
                                        'username': None,
                                        'name': '',
                                        'workerid': 0,
                                        'promocode': None
                                    })[0]
    await User.filter(id=args).update(blocked=False)
    await message.answer('Юзер {}с id {} разблокирован'.format(f'{user.username} ' if user.username else '', args))



def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(admin_menu, ChatTypeFilter(types.chat.ChatType.PRIVATE), commands=['start'],
                                is_admin=True, state='*')
    dp.register_message_handler(cancel_state, ChatTypeFilter(types.chat.ChatType.PRIVATE), commands=['cancel'],
                                is_admin=True, state='*')
    dp.register_message_handler(block_user, ChatTypeFilter(types.chat.ChatType.PRIVATE), commands=['blockuser'],
                                is_admin=True, state='*')
    dp.register_message_handler(block_user, ChatTypeFilter(types.chat.ChatType.PRIVATE), commands=['unblockuser'],
                                is_admin=True, state='*')
    dp.register_message_handler(add_worker, ChatTypeFilter(types.chat.ChatType.PRIVATE), commands=['addworker'],
                                is_admin=True, state='*')
    dp.register_message_handler(add_admin, ChatTypeFilter(types.chat.ChatType.PRIVATE), commands=['addadmin'],
                                is_admin=True, state='*')
    dp.register_message_handler(remove_admin, ChatTypeFilter(types.chat.ChatType.PRIVATE), commands=['deladmin'],
                                is_admin=True, state='*')
    dp.register_message_handler(add_worker, ChatTypeFilter(types.chat.ChatType.PRIVATE), Text(startswith='/addworker'),
                                is_admin=True, state='*')
    dp.register_message_handler(remove_worker, ChatTypeFilter(types.chat.ChatType.PRIVATE), commands=['delworker'],
                                is_admin=True, state='*')
    dp.register_message_handler(remove_worker, ChatTypeFilter(types.chat.ChatType.PRIVATE), Text(startswith='/delworker'),
                                is_admin=True, state='*')
    dp.register_message_handler(goods_menu, ChatTypeFilter(types.chat.ChatType.PRIVATE), Text(equals='📦 Товары'),
                                is_admin=True, state='*')
    dp.register_message_handler(stats_menu, ChatTypeFilter(types.chat.ChatType.PRIVATE), Text(equals='📊 Статистика'),
                                is_admin=True, state='*')
    dp.register_message_handler(promos_admin_menu, ChatTypeFilter(types.chat.ChatType.PRIVATE),
                                Text(equals='🎟️ Промокоды'), is_admin=True, state='*')
    dp.register_message_handler(workers_list_menu, ChatTypeFilter(types.chat.ChatType.PRIVATE),
                                Text(equals='👷 Воркеры'), is_admin=True, state='*')
    dp.register_callback_query_handler(workers_list_menu, lambda callback_query: callback_query.data.startswith('workers_list_'), ChatTypeFilter(types.chat.ChatType.PRIVATE),
                                is_admin=True, state='*')
    dp.register_message_handler(method_pay_edit_menu, ChatTypeFilter(types.chat.ChatType.PRIVATE),
                                Text(equals='📋 Текст оплаты'), is_admin=True, state='*')
    dp.register_message_handler(links_edit_menu, ChatTypeFilter(types.chat.ChatType.PRIVATE),
                                Text(equals='🔗 Ссылки'), is_admin=True, state='*')
    dp.register_callback_query_handler(edit_link_chosen,
                                       lambda callback_query: callback_query.data.startswith('link_change_'), is_admin=True, state='*')
    dp.register_message_handler(edit_link_text_received, state=states.admin.ChangingLink.waiting_for_link)
    dp.register_callback_query_handler(change_method_text,
                                       lambda callback_query: callback_query.data == 'change_method_text', is_admin=True, state='*')
    dp.register_message_handler(new_method_pay_received, state=states.admin.ChangingMethodText.waiting_for_text)
    dp.register_callback_query_handler(clear_users, lambda callback_query: callback_query.data == 'clear_users')
    dp.register_message_handler(adding_city_name_entered, state=states.admin.AddingCity.waiting_for_name)
    dp.register_message_handler(adding_area_name_entered, state=states.admin.AddingArea.waiting_for_name)
    dp.register_callback_query_handler(adding_position_good_chosen,
                                       lambda callback_query: callback_query.data.startswith('show_good_'),
                                       state=states.admin.AddingPosition.waiting_for_good)
    dp.register_message_handler(adding_position_weight_entered, ChatTypeFilter(types.chat.ChatType.PRIVATE),
                                state=states.admin.AddingPosition.waiting_for_weight)
    dp.register_message_handler(adding_position_type_entered, ChatTypeFilter(types.chat.ChatType.PRIVATE),
                                state=states.admin.AddingPosition.waiting_for_type)
    dp.register_message_handler(adding_position_price_entered, ChatTypeFilter(types.chat.ChatType.PRIVATE),
                                state=states.admin.AddingPosition.waiting_for_price)
    dp.register_message_handler(good_name_entered, ChatTypeFilter(types.chat.ChatType.PRIVATE),
                                state=states.admin.AddingGood.waiting_for_name)
    dp.register_message_handler(good_description_entered, ChatTypeFilter(types.chat.ChatType.PRIVATE),
                                state=states.admin.AddingGood.waiting_for_description)
    dp.register_message_handler(good_photo_sent, ChatTypeFilter(types.chat.ChatType.PRIVATE),
                                state=states.admin.AddingGood.waiting_for_photo,
                                content_types=ContentType.ANY)
    dp.register_callback_query_handler(confirm_zalet,
                                       lambda callback_query: any([callback_query.data.startswith(x) for x in
                                                                   ['decline_zalet_', 'accept_zalet_']]))
    dp.register_callback_query_handler(city_edit,
                                       lambda callback_query: any([callback_query.data.startswith(x) for x in
                                                                   ['remove_city_', 'hide_city_', 'unhide_city_',
                                                                    'add_city']]))
    dp.register_callback_query_handler(area_edit,
                                       lambda callback_query: any([callback_query.data.startswith(x) for x in
                                                                   ['unhide_area_', 'hide_area_', 'remove_area_',
                                                                    'add_area_']]), state='*')
    dp.register_callback_query_handler(position_edit,
                                       lambda callback_query: any([callback_query.data.startswith(x) for x in
                                                                   ['unhide_position_', 'hide_position_',
                                                                    'remove_position_', 'add_position_']]), state='*')
    dp.register_callback_query_handler(goods_menu, lambda callback_query: callback_query.data.startswith('goods_menu'))
    dp.register_callback_query_handler(show_good_menu,
                                       lambda callback_query: callback_query.data.startswith('show_good_'))
    dp.register_callback_query_handler(edit_good,
                                       lambda callback_query: any([callback_query.data.startswith(x) for x in
                                                                   ['remove_good_', 'unhide_good_', 'hide_good_',
                                                                    'add_good']]))
    # dp.register_message_handler(start_cmd, commands=['start'], state='*')
    # dp.register_message_handler(save_cmd, commands=['save_file'], state='*')
    # dp.register_message_handler(date_chosen, state=AddingClient.waiting_for_date)
