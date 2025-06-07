from aiogram import Router, types
from aiogram.filters import CommandStart

from db.models import User
from bot.keyboards.default import main_menu

# Create router for /start command
router = Router()


@router.message(CommandStart())
async def start_handler(message: types.Message, db_session):
    """
    Handler for /start command.

    Checks if user is registered and creates new database entry for new users.
    Provides welcome message with current balance and available commands.

    Args:
        message: Message object containing user info
        db_session: Database session for user operations

    Behavior:
        - For existing users: shows welcome back message with balance
        - For new users: creates database record and initial welcome
        - Always provides main menu keyboard
    """
    # Open database session via context manager
    with db_session as db:
        # Search for user by username
        user = db.query(User).filter(User.username ==
                                     message.from_user.username).first()

        if user:
            # Existing user greeting with current balance
            await message.answer(
                f"<b>Hi!, This is a convenient bot for buying gifts in Telegram.</b>\n\n"
                f"With us, you can instantly and automatically purchase new gifts and enjoy peaceful sleep knowing everything’s taken care of.\n\n"
                f"<b>Your balance:</b> {user.balance}⭐️\n\n",
                reply_markup=main_menu()
            )
        else:
            # Create new user record
            new_user = User(
                user_id=message.from_user.id,
                username=message.from_user.username
            )
            db.add(new_user)
            db.commit()
            await message.answer(
                f"<b>Hi!, This is a convenient bot for buying gifts in Telegram.</b>\n\n"
                f"With us, you can instantly and automatically purchase new gifts and enjoy peaceful sleep knowing everything’s taken care of.\n\n"
                f"<b>Your balance:</b> 0⭐️\n\n",
                reply_markup=main_menu()
            )
