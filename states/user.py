from aiogram.dispatcher.filters.state import State, StatesGroup


class UsingPromo(StatesGroup):
    waiting_for_promo = State()