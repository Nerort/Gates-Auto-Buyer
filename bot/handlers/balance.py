import aiohttp
from datetime import datetime
from aiogram import types, Router, Bot, F
from aiogram.filters import Command, StateFilter, CommandObject
from aiogram.fsm.context import FSMContext

from api.gifts import GiftsApi
from utils.logger import log
from bot.states.deposit_state import DepositStates
from bot.keyboards.default import balance_menu, main_menu, go_back_menu
from bot.keyboards.inline import payment_keyboard
from db.models import User, Transaction

router = Router()
gifts_api = GiftsApi()


# Utility Functions
@log.catch
async def get_user_by_username(db_session, username: str) -> User | None:
    """
    Retrieve a user by their username from the database.

    Args:
        db_session: Database session
        username: Telegram username to search for

    Returns:
        User: User object if found
        None: If user doesn't exist
    """
    with db_session as db:
        return db.query(User).filter(User.username == username).first()


@log.catch
async def get_user_by_id(db_session, user_id: int) -> User | None:
    """
    Retrieve a user by their Telegram ID from the database.

    Args:
        db_session: Database session
        user_id: Telegram user ID to search for

    Returns:
        User: User object if found
        None: If user doesn't exist
    """
    with db_session as db:
        return db.query(User).filter(User.user_id == user_id).first()


@log.catch
async def return_to_main_menu(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Return user to the main menu and clear current state.

    Args:
        callback: Callback object to respond to
        state: Current FSM state to clear
    """
    await state.clear()
    await callback.message.answer(
        text="You've returned to the main menu! Please use the buttons below to continue.",
        reply_markup=main_menu()
    )


@log.catch
async def return_to_main_menu_msg(message: types.Message, state: FSMContext) -> None:
    """
    Return user to the main menu and clear current state.

    Args:
        message: Callback object to respond to
        state: Current FSM state to clear
    """
    await state.clear()
    await message.answer(
        text="You've returned to the main menu! Please use the buttons below to continue.",
        reply_markup=main_menu()
    )


# Handlers
@log.catch
@router.callback_query(F.data == 'balance')
async def get_balance_command(callback: types.CallbackQuery, db_session) -> None:
    """
    Display the user's current balance.

    Args:
        callback: Incoming message object
        db_session: Database session

    Behavior:
        - Retrieves user from database
        - Displays balance with formatted message
        - Shows balance menu keyboard
    """
    user = await get_user_by_username(db_session, callback.from_user.username)
    if not user:
        await callback.reply("User not found. Please try again.")
        return

    await callback.message.answer(
        f"👤<b>Your Profile:</b> {callback.from_user.username} \n\n<b>Balance:</b> {user.balance}⭐️",
        reply_markup=balance_menu()
    )

# # Handlers
# @log.catch
# @router.message(Command(commands=["balance"]))
# async def get_balance_command(message: types.Message, db_session) -> None:
#     """
#     Display the user's current balance.
#
#     Args:
#         message: Incoming message object
#         db_session: Database session
#
#     Behavior:
#         - Retrieves user from database
#         - Displays balance with formatted message
#         - Shows balance menu keyboard
#     """
#     user = await get_user_by_username(db_session, message.from_user.username)
#     if not user:
#         await message.reply("User not found. Please try again.")
#         return
#
#     await message.answer(
#         f"Your balance: {user.balance}⭐️",
#         reply_markup=balance_menu()
#     )


@log.catch
@router.callback_query(F.data == 'back')
async def go_back_in_menu(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Command handler to return to main menu from any state.

    Args:
        callback: Incoming message object
        state: Current FSM state to clear
    """
    await return_to_main_menu(callback, state)


@log.catch
@router.callback_query(F.data == 'deposit')
async def deposit_command(callback: types.CallbackQuery, state: FSMContext, db_session) -> None:
    """
    Initiate the deposit process.

    Args:
        callback: Incoming message object
        state: Current FSM state
        db_session: Database session

    Transitions:
        Sets state to DepositStates.waiting_for_amount_deposit

    Behavior:
        - Verifies user exists
        - Shows current balance
        - Requests deposit amount input
    """
    user = await get_user_by_username(db_session, callback.from_user.username)
    if not user:
        await callback.message.reply("User not found. Please try again.")
        return

    await callback.message.answer(
        text=f"<b>Your balance:</b> {user.balance}⭐️\n\nEnter deposit amount (numbers only).\nExample: 15",
        reply_markup=go_back_menu()
    )
    await state.set_state(DepositStates.waiting_for_amount_deposit)


@log.catch
@router.message(StateFilter(DepositStates.waiting_for_amount_deposit))
async def process_deposit_input(message: types.Message, state: FSMContext) -> None:
    """
    Process deposit amount input and generate payment invoice.

    Args:
        message: Incoming message with amount
        state: Current FSM state

    Validates:
        - Positive integer input
        - Non-zero amount

    On Success:
        - Generates payment invoice
        - Clears state

    On Failure:
        - Shows error message
        - Maintains state for retry
    """
    if message.text == "🔙 Back":
        await return_to_main_menu_msg(message, state)
        return

    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError("Amount must be positive.")
    except ValueError:
        await message.reply("Please enter a positive number. Example: 15")
        return

    payload = f"deposit_{amount}_to_{message.from_user.id}"

    log.info(
        f"Creating deposit for amount {amount} from user {message.from_user.id}")

    prices = [types.LabeledPrice(label="Deposit", amount=amount)]
    await message.answer_invoice(
        title="Deposit",
        description="Adding funds to your account",
        payload=payload,
        currency="XTR",
        prices=prices,
        provider_token="",
        reply_markup=payment_keyboard(price=amount)
    )
    await state.clear()


@log.catch
@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: types.PreCheckoutQuery) -> None:
    """
    Handle pre-checkout query for payment validation.

    Args:
        pre_checkout_query: Telegram pre-checkout query object

    Behavior:
        - Always approves payment (ok=True)
        - Actual validation happens in process_deposit_payment
    """
    await pre_checkout_query.answer(ok=True)


@log.catch
async def process_deposit_payment(message: types.Message, db_session, payment_info: types.SuccessfulPayment) -> None:
    """
    Process successful deposit payment and update user balance.

    Args:
        message: Message object with payment info
        db_session: Database session
        payment_info: SuccessfulPayment object from Telegram

    Behavior:
        - Parses payment payload
        - Updates user balance
        - Creates transaction record
        - Sends confirmation message

    On Error:
        - Logs detailed error
        - Sends user-friendly error message
    """
    payload = payment_info.invoice_payload
    parts = payload.split("_")
    amount = int(parts[1])
    user_id = int(parts[3])

    try:
        with db_session as db:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise ValueError("User not found.")

            user.balance += amount

            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                telegram_payment_charge_id=payment_info.telegram_payment_charge_id,
                status="completed",
                time=datetime.now().isoformat(),
                payload=payload  # Saving payload in transaction
            )
            db.add(transaction)
            db.commit()

        await message.reply(
            f"Deposit of {amount}⭐️ successfully credited to your account.",
            reply_markup=main_menu()
        )
    except Exception as e:
        log.error(f"Deposit processing error: {e}")
        await message.reply("Error processing your deposit. Please try again later.")


@log.catch
@router.message(Command("refund"))
async def command_refund_handler(message: types.Message, bot: Bot, command: CommandObject, db_session) -> None:
    """
    Handle refund command for administrators.

    Args:
        message: Incoming message object
        bot: Bot instance for API calls
        command: Parsed command object with arguments
        db_session: Database session

    Workflow:
        1. Verify admin privileges
        2. Validate transaction exists
        3. Process refund via Telegram API
        4. Update database records
        5. Confirm completion

    Error Handling:
        - Detailed error logging
        - User-friendly error messages
    """
    transaction_id = command.args
    if not transaction_id:
        await message.reply("Please specify transaction ID for refund.")
        return

    try:
        with db_session as db:
            admin_user = db.query(User).filter(
                User.user_id == message.from_user.id).first()
            if not admin_user or admin_user.status != "admin":
                await message.reply("You don't have permission to execute this command.")
                return

            transaction = db.query(Transaction).filter(
                Transaction.telegram_payment_charge_id == transaction_id
            ).first()

            if not transaction:
                await message.reply("Transaction not found. Please check ID and try again.")
                return

            if transaction.status == "refunded":
                await message.reply("Funds for this transaction were already refunded.")
                return

            user = db.query(User).filter(
                User.user_id == transaction.user_id).first()
            if not user:
                await message.reply("User associated with transaction not found.")
                return

            refund_amount = transaction.amount
            target_user_id = transaction.user_id

        try:
            result = await bot.refund_star_payment(
                user_id=target_user_id,
                telegram_payment_charge_id=transaction_id
            )
            log.debug(result)
        except Exception as e:
            log.error(f"Error processing refund via Telegram API: {e}")
            await message.reply("Refund processing via Telegram API failed, please contact support.")
            return

        with db_session as db:
            transaction = db.query(Transaction).filter(
                Transaction.telegram_payment_charge_id == transaction_id
            ).first()

            if not transaction:
                await message.reply("Failed to find transaction for update. Please contact support.")
                return

            user = db.query(User).filter(
                User.user_id == transaction.user_id).first()
            if not user:
                await message.reply("Failed to find user for balance update. Please contact support.")
                return

            transaction.status = "refunded"
            user.balance -= refund_amount
            db.commit()

        await message.reply(
            f"Refund for transaction ID: {transaction_id} processed successfully. Refund amount: {refund_amount}⭐️."
        )

    except Exception as e:
        log.error(f"Refund processing error: {e}")
        await message.reply(f"Error processing refund: {e}")
