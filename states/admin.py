from aiogram.dispatcher.filters.state import State, StatesGroup

class ChangingMethodText(StatesGroup):
    waiting_for_text = State()

class ChangingLink(StatesGroup):
    waiting_for_link = State()

class AddingGood(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_photo = State()


class AddingCity(StatesGroup):
    waiting_for_name = State()


class AddingArea(StatesGroup):
    waiting_for_name = State()


class AddingPosition(StatesGroup):
    waiting_for_good = State()
    waiting_for_weight = State()
    waiting_for_type = State()
    waiting_for_price = State()
