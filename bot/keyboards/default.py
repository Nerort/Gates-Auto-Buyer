from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu():
    """
    Creates main menu keyboard with core functionality buttons.

    Returns:
        ReplyKeyboardMarkup: Keyboard with buttons for:
        - Balance check
        - Gift purchase
        - Deposit funds
        - Start command
        - Auto-buy setup
    """

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⭐️ Deposit Balance', callback_data='deposit')],
            [
                InlineKeyboardButton(text='👤 Profile', callback_data='balance'),
                InlineKeyboardButton(text="🎁 Buy Gift", callback_data='buy-gift'),
            ],
            [
                InlineKeyboardButton(text='⚙️ Auto-Buy Settings', callback_data='auto-buy')
            ]
        ],
        resize_keyboard=True
    )
    return markup


def balance_menu():
    """
    Creates balance management keyboard.

    Returns:
        ReplyKeyboardMarkup: Keyboard with buttons for:
        - Adding funds
        - Returning to main menu
    """
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⭐️ Deposit Balance', callback_data='deposit')],
            [InlineKeyboardButton(text="🔙 Back", callback_data='back')]
        ],
        resize_keyboard=True
    )
    return markup


def go_back_menu():
    """
    Creates minimal keyboard with return to main menu option.

    Returns:
        ReplyKeyboardMarkup: Single button for navigation back
    """
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔙 Back")
            ],
        ],
        resize_keyboard=True
    )
    return markup


def auto_buy_keyboard():
    """
    Creates auto-purchase configuration keyboard.

    Returns:
        ReplyKeyboardMarkup: Keyboard with buttons for:
        - Toggle auto-purchase
        - Price limit setup
        - Supply limit setup
        - Cycles configuration
        - Main menu return
    """
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔄 Toggle On/Off")
            ],
            [
                KeyboardButton(text="✏️ Price Limit"),
                KeyboardButton(text="✏️ Supply Limit"),
                KeyboardButton(text="✏️ Number of Cycles"),
            ],
            [
                KeyboardButton(text="🔙 Back to Main Menu")
            ]
        ],
        resize_keyboard=True
    )
    return markup


def auto_buy_price_keyboard():
    """
    Creates price limit setup keyboard.

    Returns:
        ReplyKeyboardMarkup: Keyboard with single button for:
        - Returning to main menu
    """
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Back to Main Menu")]
        ],
        resize_keyboard=True
    )
    return markup


def auto_buy_supply_keyboard():
    """
    Creates supply limit setup keyboard.

    Returns:
        ReplyKeyboardMarkup: Keyboard with single button for:
        - Returning to main menu
    """
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Back to Main Menu")]
        ],
        resize_keyboard=True
    )
    return markup
