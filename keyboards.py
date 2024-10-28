from aiogram.types import \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

from models import Promocode, City, Area, Position, Good, paySystem
from utils.config import config
from utils.utils import Access


def main_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup()
    kb.row(KeyboardButton("🏠 Города"), KeyboardButton("🆘 Поддержка"))
    kb.row(KeyboardButton("👤 Вакансии"), KeyboardButton("🛒 Предзаказ"))
    kb.row(KeyboardButton("💾 История заказов"), KeyboardButton("📖 Отзывы | Гарантии"))
    kb.row(KeyboardButton("📚 Правила"), KeyboardButton("🗣️ Чат клиентов"))
    return kb


def worker_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('📊 Статистика', callback_data='stats_menu'))
    kb.add(InlineKeyboardButton('🎟️ Промокоды', callback_data='promos_menu'))
    return kb


def admin_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup()
    kb.row(KeyboardButton('🏠 Города'), KeyboardButton('📦 Товары'))
    kb.row(KeyboardButton('📊 Статистика'), KeyboardButton('👷 Воркеры'))
    # kb.row(KeyboardButton('🎟️ Промокоды'), KeyboardButton('📋 Текст оплаты'))
    kb.row(KeyboardButton('📋 Текст оплаты'), KeyboardButton('🔗 Ссылки'))
    return kb


def single_url_inline(text) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(text, url='http://t.me/' + config.links.admin_username))
    return kb


def support_inline() -> InlineKeyboardMarkup:
    return single_url_inline('👨‍💻 Написать оператору')


def vacancies_inline() -> InlineKeyboardMarkup:
    return single_url_inline('💰 Получить работу 💰')


def preorder_inline() -> InlineKeyboardMarkup:
    return single_url_inline('📝 Отправить заявку')


def reviews_inline() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('📚 Правила', callback_data='review'))
    kb.add(InlineKeyboardButton('📍 Официальный канал 📍', url=config.links.reviews_channel_url))
    return kb


async def generate_cities_inline(user, access) -> InlineKeyboardMarkup:
    cities = City.filter(hidden=0).order_by('name') if access == Access.USER else City.all().order_by('name')
    promocode = await Promocode.get_or_none(id=user.promocode)
    cities_id = [int(x) for x in promocode.cities.strip('|').split('|')] if promocode and promocode.cities else None
    keyboard = InlineKeyboardMarkup()
    async for city in cities:
        if cities_id and city.id not in cities_id:
            continue
        keyboard.add(InlineKeyboardButton('{}🏡 {}'.format('🚫' if city.hidden else '', city.name),
                                          callback_data='city_{}'.format(city.id)))
    if access == Access.ADMIN:
        keyboard.add(InlineKeyboardButton('➕ Добавить город', callback_data='add_city'))
    return keyboard


async def generate_areas_inline(city, access) -> InlineKeyboardMarkup:
    areas = Area.filter(hidden=0, city=city).order_by('name') if access == Access.USER else Area.filter(city=city).order_by('name')
    city = await City.get(id=int(city))
    keyboard = InlineKeyboardMarkup()
    async for area in areas:
        keyboard.add(InlineKeyboardButton('{}📂 {}'.format('🚫' if area.hidden else '', area.name),
                                          callback_data='area_{}'.format(area.id)))
    if access == Access.ADMIN:
        keyboard.add(InlineKeyboardButton('🗑️ Удалить город', callback_data='remove_city_{}'.format(city.id)))
        if not city.hidden:
            keyboard.add(InlineKeyboardButton('🚫 Скрыть город', callback_data='hide_city_{}'.format(city.id)))
        else:
            keyboard.add(InlineKeyboardButton('➕ Раскрыть город', callback_data='unhide_city_{}'.format(city.id)))
        keyboard.add(InlineKeyboardButton('➕ Добавить район', callback_data='add_area_{}'.format(city.id)))
    keyboard.add(InlineKeyboardButton('🔙 Назад', callback_data='cities'))
    return keyboard


def worker_stats_inline():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('🔙 Назад', callback_data='worker_menu'))
    return keyboard


async def generate_goods_inline(area_id, access) -> InlineKeyboardMarkup:
    # positions = Position.filter(area=area, hidden=0) if access == Access.USER else Position.filter(area=area)
    # goods = list()
    # async for position in positions:
    #     good = await position.good.first()
    #     if good not in goods:
    #         if access == Access.ADMIN or not good.hidden:
    #             goods.append(good)
    if access == Access.USER:
        good_ids = [x['good__id'] for x in await Position.filter(area=area_id, hidden=0).distinct().values('good__id')]
        goods = await Good.filter(id__in=good_ids, hidden=0).order_by('name')
    else:
        good_ids = [x['good__id'] for x in await Position.filter(area=area_id).distinct().values('good__id')]
        goods = await Good.filter(id__in=good_ids).order_by('name')
    keyboard = InlineKeyboardMarkup()
    for good in goods:
        keyboard.add(InlineKeyboardButton('{}📦 {}'.format('🚫' if good.hidden else '', good.name),
                                          callback_data='good_{}_{}'.format(good.id, area_id)))
    area_id = await Area.get(id=area_id)
    if access == Access.ADMIN:
        keyboard.add(InlineKeyboardButton('🗑️ Удалить район', callback_data='remove_area_{}'.format(area_id.id)))
        if not area_id.hidden:
            keyboard.add(InlineKeyboardButton('🚫 Скрыть район', callback_data='hide_area_{}'.format(area_id.id)))
        else:
            keyboard.add(InlineKeyboardButton('➕ Раскрыть район', callback_data='unhide_area_{}'.format(area_id.id)))
        keyboard.add(InlineKeyboardButton('➕ Добавить позицию', callback_data='add_position_{}'.format(area_id.id)))
    city = await area_id.city.first()
    keyboard.add(InlineKeyboardButton('🔙 Назад', callback_data='city_{}'.format(city.id)))
    return keyboard


async def generate_goods_admin_inline() -> InlineKeyboardMarkup:  # Goods menu for admin
    goods = Good.all().order_by('name')
    keyboard = InlineKeyboardMarkup()
    async for good in goods:
        keyboard.add(InlineKeyboardButton('{}📦 {}'.format('🚫' if good.hidden else '', good.name),
                                          callback_data='show_good_{}'.format(good.id)))
    keyboard.add(InlineKeyboardButton('➕ Добавить товар', callback_data='add_good'))
    return keyboard


async def generate_good_edit_inline(good_id) -> InlineKeyboardMarkup:
    good = await Good.get(id=good_id)
    keyboard = InlineKeyboardMarkup()
    if good.hidden:
        keyboard.add(InlineKeyboardButton('➕ Раскрыть товар', callback_data='unhide_good_{}'.format(good.id)))
    else:
        keyboard.add(InlineKeyboardButton('🚫 Скрыть товар', callback_data='hide_good_{}'.format(good.id)))
    keyboard.add(InlineKeyboardButton('🗑️ Удалить товар', callback_data='remove_good_{}'.format(good.id)))
    keyboard.add(InlineKeyboardButton('🔙 Назад', callback_data='goods_menu'))
    return keyboard


async def generate_positions_inline(good: Good, area: int, access: Access) -> InlineKeyboardMarkup:
    if access is Access.USER:
        positions = Position.filter(good=good, area=area, hidden=0).order_by('weight')
    else:
        positions = Position.filter(good=good, area=area).order_by('weight')
    keyboard = InlineKeyboardMarkup()
    async for position in positions:
        keyboard.add(InlineKeyboardButton('{}🔍 {} | {} | {} руб'.format('🚫' if position.hidden else '',
                                                                         position.weight,
                                                                         position.type,
                                                                         position.price),
                                          callback_data='position_{}'.format(position.id)))
    # if access == Access.admin:
    #     keyboard.append([Button.inline('🗑️ Удалить весь товар в районе', callback_data='remove_good_{}_{}'.format(area, good))])
    #     if not area.hidden:
    #         keyboard.append([Button.inline('🚫 Скрыть весь товар в районе', callback_data='hide_good_{}_{}'.format(area, good))])
    #     else:
    #         keyboard.append([Button.inline('➕ Раскрыть весь товар в районе', callback_data='unhide_good_{}_{}'.format(area, good))])
    keyboard.add(InlineKeyboardButton('🔙 Назад', callback_data='area_{}'.format(area)))
    return keyboard


async def confirmation_zalet_inline(zalet_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('✅ Подтвердить залёт', callback_data='accept_zalet_{}'.format(zalet_id)))
    keyboard.add(InlineKeyboardButton('❌ Отклонить залёт', callback_data='decline_zalet_{}'.format(zalet_id)))
    return keyboard


async def generate_promo_inline(position, user, access=None) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    position_object = await Position.get_or_none(id=position)
    if not position_object:
        return
    good = await position_object.good.first()
    area = position_object.area
    # TODO добавить кнопку с промокодом
    if access == Access.USER:
        promocode = None
        if user.promocode:
            promocode = await Promocode.get_or_none(id=user.promocode)
        if promocode:
            keyboard.add(InlineKeyboardButton('🎟️ {} | Скидка {}%'.format(promocode.code, promocode.discount),
                                              callback_data='pay_{}_discount_{}'.format(position, promocode.discount)))
        else:
            keyboard.add(InlineKeyboardButton('❌ Нет промокода', callback_data='pay_{}'.format(position)))
    elif access == Access.ADMIN:
        keyboard.add(InlineKeyboardButton('🗑️ Удалить позицию', callback_data='remove_position_{}'.format(position)))
        if not position_object.hidden:
            keyboard.add(InlineKeyboardButton('🚫 Скрыть позицию', callback_data='hide_position_{}'.format(position)))
        else:
            keyboard.add(
                InlineKeyboardButton('➕ Раскрыть позицию', callback_data='unhide_position_{}'.format(position)))
    keyboard.add(InlineKeyboardButton('🔙 Назад', callback_data='good_{}_{}'.format(good.id, area)))
    return keyboard


async def admin_stats_inline() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton('❌ Удалить неактивных юзеров', callback_data='clear_users')
    )
    return keyboard


async def generate_payout_inline() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    methods = await paySystem.all()  # Чо это за метод?
    keyboard.add(
        InlineKeyboardButton('👨‍💻 Написать оператору', url='https://t.me/{}'.format(config.links.support_username)))
    return keyboard


async def generate_worker_promos_inline(worker) -> InlineKeyboardMarkup:
    promos = Promocode.filter(workerid=worker)
    keyboard = InlineKeyboardMarkup()
    async for promocode in promos:
        keyboard.add(InlineKeyboardButton('🎟️ {}% {} '.format(promocode.discount, promocode.code),
                                          callback_data='edit_promo_{}'.format(promocode.id)))
    keyboard.add(InlineKeyboardButton('➕ Создать промокод', callback_data='generate_promo'))
    keyboard.add(InlineKeyboardButton('🔙 Назад', callback_data='worker_menu'))
    return keyboard


async def generate_promo_edit_inline(promocode_id) -> InlineKeyboardMarkup:
    promocode = await Promocode.get(id=promocode_id)
    keyboard = InlineKeyboardMarkup()
    discount = list()
    discount.append(InlineKeyboardButton('3%', callback_data='set_promo_discount_{}_{}'.format(promocode.id, 3)))
    discount.append(InlineKeyboardButton('5%', callback_data='set_promo_discount_{}_{}'.format(promocode.id, 5)))
    discount.append(InlineKeyboardButton('10%', callback_data='set_promo_discount_{}_{}'.format(promocode.id, 10)))
    discount.append(InlineKeyboardButton('15%', callback_data='set_promo_discount_{}_{}'.format(promocode.id, 15)))
    discount.append(InlineKeyboardButton('20%', callback_data='set_promo_discount_{}_{}'.format(promocode.id, 20)))
    keyboard.add(*discount)
    keyboard.add(InlineKeyboardButton('Выбрать города для промо',
                                      callback_data='choose_cities_promo_{}'.format(promocode.id)))
    keyboard.add(InlineKeyboardButton('🗑️ Удалить промо', callback_data='remove_promo_{}'.format(promocode.id)))
    keyboard.add(InlineKeyboardButton('🔙 Назад', callback_data='promos_menu'))
    return keyboard


async def generate_promo_cities_inline(promocode_id) -> InlineKeyboardMarkup:
    promocode = await Promocode.get(id=promocode_id)
    cities_id = [int(x) for x in promocode.cities.strip('|').split('|')] if promocode.cities else None
    if cities_id:
        all_cities = False
    else:
        all_cities = True
    cities_obj = City.all()
    keyboard = InlineKeyboardMarkup()
    async for city in cities_obj:
        keyboard.add(InlineKeyboardButton('{}🏡 {}'.format('🚫' if not all_cities and city.id not in cities_id else '',
                                                           city.name),
                                          callback_data='promo_{}_city_{}_{}'.format(
                                              'remove' if not all_cities and city.id in cities_id else 'add',
                                              promocode_id, city.id)))
    keyboard.add(InlineKeyboardButton('🔙 Назад', callback_data='edit_promo_{}'.format(promocode_id)))
    return keyboard


async def generate_workers_list_inline(page, total) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    if page > 1:
        keyboard.insert(InlineKeyboardButton('<', callback_data=f'workers_list_{page-1}'))
    keyboard.insert(InlineKeyboardButton(f'{page}/{total}', callback_data=f'workers_list_{page}'))
    if page < total:
        keyboard.insert(InlineKeyboardButton('>', callback_data=f'workers_list_{page+1}'))
    return keyboard


async def generate_links_menu_inline() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Изменить юзернейм админа', callback_data='link_change_admin_username'))
    keyboard.add(InlineKeyboardButton('Изменить юзернейм оператора', callback_data='link_change_operator_username'))
    keyboard.add(InlineKeyboardButton('Изменить ID отстука', callback_data='link_change_forward_channel_id'))
    keyboard.add(InlineKeyboardButton('Изменить ID залётов', callback_data='link_change_zalets_channel_id'))
    keyboard.add(InlineKeyboardButton('Изменить ссылку на отзывы', callback_data='link_change_reviews_channel_url'))
    return keyboard

async def generate_stats_worker_inline() -> InlineKeyboardMarkup:
    pass

async def method_pay_inline()  -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Изменить текст', callback_data='change_method_text'))
    return keyboard

@property
def back_button():
    kb = ReplyKeyboardMarkup()
    kb.row(KeyboardButton('🔙 Назад'))
    return kb


# Как это работает?
async def generate_order_inline(user) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Проверить оплату ✅', callback_data='checkorder_{}'.format(user.id)))
    keyboard.add(InlineKeyboardButton('🆘 Поддержка', url='https://t.me/{}'.format(config.links.admin_username)))


def get_kb(key: str) -> InlineKeyboardMarkup:
    kbs = {
        'startreply': main_keyboard,
        'startinline': reviews_inline,
        'support': support_inline,
        'vacancies': vacancies_inline,
        'preorder': preorder_inline,
        'reviews': reviews_inline,
    }
    kb = kbs.get(key, None)
    if kb:
        return kb()
    else:
        return None
