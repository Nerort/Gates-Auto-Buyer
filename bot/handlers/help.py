from aiogram import types, Router
from aiogram.filters import Command

router = Router()


@router.message(Command(commands=["help"]))
async def help_command(message: types.Message):
    """
    Handles the /help command to provide user assistance.

    Args:
        message: The incoming message object containing the command

    Replies with:
        - Basic instructions to use /start command
        - Contact information for support
    """
    await message.reply("Type /start to begin.")
