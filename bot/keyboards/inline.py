from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def payment_keyboard(price):
    builder = InlineKeyboardBuilder()
    builder.button(text=f'Оплатить {price}⭐️')
