from aiogram.fsm.state import StatesGroup, State


class AutoBuyStates(StatesGroup):
    menu = State()
    set_price = State()
    set_supply = State()
    set_cycles = State()
