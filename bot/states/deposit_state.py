from aiogram.fsm.state import StatesGroup, State


class DepositStates(StatesGroup):
    waiting_for_amount_deposit = State()
