from aiogram.fsm.state import StatesGroup, State


class GiftStates(StatesGroup):
    waiting_for_gift_id = State()
