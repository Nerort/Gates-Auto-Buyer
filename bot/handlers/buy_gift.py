from datetime import datetime

import aiohttp
from aiogram import types, Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from api.gifts import GiftsApi
from utils.logger import log
from bot.states.gift_state import GiftStates
from bot.keyboards.inline import payment_keyboard
from bot.keyboards.default import go_back_menu, main_menu
from db.models import User, Transaction

router = Router()
gifts_api = GiftsApi()


@log.catch
async def return_to_main_menu(message: types.Message, state: FSMContext) -> None:
    """
    Return user to main menu and clear current state.

    Args:
        message: Message object to respond to
        state: Current FSM state to clear

    Behavior:
        - Clears any active state
        - Sends return confirmation message
        - Displays main menu keyboard
    """
    await state.clear()
    await message.answer(
        text='You have returned to the main menu! Please use the buttons below to continue.',
        reply_markup=main_menu()
    )


@log.catch
async def fetch_gifts_list() -> list | None:
    """
    Fetch available gifts list from API.

    Returns:
        list: List of available gifts if successful
        None: If error occurs

    Raises:
        Exception: Logs any API errors but doesn't propagate them
    """
    try:
        async with aiohttp.ClientSession() as session:
            return await gifts_api.aio_get_available_gifts(session=session)
    except Exception as e:
        log.error(f"Error fetching gifts list: {e}")
        return None


@log.catch
async def process_gift_payment(
    message: types.Message,
    db_session,
    payment_info: types.SuccessfulPayment = None,
    from_balance: bool = False
) -> None:
    """
    Process gift payment and send gifts to recipient.

    Args:
        message: Message object containing payment info
        db_session: Database session
        payment_info: SuccessfulPayment object (for external payments)
        from_balance: Flag indicating balance payment

    Workflow:
        1. Parse payment details from payload/message
        2. Validate gift ID and price
        3. Send gifts via API
        4. Record transaction
        5. Confirm completion

    Raises:
        ValueError: If gift ID is invalid or price unavailable
    """
    if not from_balance:
        payload = payment_info.invoice_payload
        parts = payload.split("_")
        gift_id = parts[1]
        user_id = parts[3]
        gifts_count = int(parts[5])
    else:
        parts = message.text.split()
        gift_id = parts[0]
        user_id = parts[1]
        gifts_count = int(parts[2])
        payload = f"gift_{gift_id}_to_{user_id}_count_{gifts_count}"
    gift_price = None
    gifts_list = await fetch_gifts_list()
    for gift in gifts_list:
        if str(gift_id) == str(gift.get('id')):
            gift_price = gift.get('star_count')

    if gift_price is None:
        raise ValueError("Invalid gift ID or price retrieval error.")

    amount = int(gift_price) * gifts_count
    telegram_payment_charge_id = 'buy_gift_transaction' if from_balance else payment_info.telegram_payment_charge_id

    try:
        with db_session as db:
            user = db.query(User).filter(
                User.user_id == message.from_user.id).first()
            if not user:
                raise ValueError("User not found in database.")

            for _ in range(gifts_count):
                result = await gifts_api.send_gift(user_id=int(user_id), gift_id=gift_id)
                if result:
                    log.info(
                        f"Gift {gift_id} successfully sent to user {user_id}.")
                else:
                    log.warning(
                        f"Error sending gift {gift_id} to user {user_id}.")
                    await message.reply(f"Error sending gift to user {user_id}. Stars were preserved.")

            transaction = Transaction(
                user_id=message.from_user.id,
                amount=amount,
                telegram_payment_charge_id=telegram_payment_charge_id,
                status="completed",
                time=datetime.now().isoformat(),
                payload=payload  # Store payload in transaction
            )
            db.add(transaction)
            db.commit()

        await message.reply(f"Gift with ID {gift_id} successfully sent to user {user_id}.")
    except Exception as e:
        log.error(f"Error processing gifts: {e}")
        await message.reply("An error occurred while processing gifts. Please try again later.")


@log.catch
@router.callback_query(F.data == 'buy-gift')
async def buy_gift_command(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Initiate gift purchase process.

    Args:
        callback: Command message object
        state: Current FSM state

    Behavior:
        1. Fetches available gifts list
        2. Displays formatted gift catalog
        3. Requests gift purchase details
        4. Sets state to wait for input
    """
    gifts_list = await fetch_gifts_list()
    if not gifts_list:
        await callback.message.reply("Currently no gifts available.")
        return

    sorted_gifts = sorted(gifts_list, key=lambda unsorted_gift: int(
        unsorted_gift.get("total_count", 0)), reverse=True)

    gift_descriptions = []
    for gift in sorted_gifts:
        # Получаем значения доступности
        remaining = gift.get("remaining_count", "Unlimited")
        total = gift.get("total_count", "Unlimited")

        # Форматируем строку доступности
        if "Unlimited" in [str(remaining), str(total)]:
            availability = "Unlimited"
        else:
            availability = f"{remaining}/{total}"

        # Формируем описание подарка
        description = (
            f'<b>Gift:</b> {gift.get("sticker", {}).get("emoji", "🎁")}\n'
            f'<b>ID:</b> <code>{gift["id"]}</code>\n'
            f'<b>Price:</b> {gift["star_count"]}⭐️\n'
            f'<b>Available:</b> {availability}\n'
        )
        gift_descriptions.append(description)

    if not gift_descriptions:
        await callback.message.reply("No gifts available.")
        return

    await callback.message.answer("\n".join(gift_descriptions), parse_mode="HTML")
    await callback.message.answer(
        text=f'\n\n💝 <b>Buy a Gift:</b>\n🔹 Gift ID\n🔹 Recipient ID  \n🔹 Quantity \n\n<i>Format:</i> <code>Gift_ID Recipient_ID Quantity</code> \n<i>Example:</i> <code>5170233102089322756 995515020 1</code>',
        reply_markup=go_back_menu()
    )
    await state.set_state(GiftStates.waiting_for_gift_id)


@log.catch
@router.message(StateFilter(GiftStates.waiting_for_gift_id))
async def process_gift_id_input(
    message: types.Message,
    state: FSMContext,
    db_session
) -> None:
    """
    Process gift purchase details and handle payment.

    Args:
        message: Message containing purchase details
        state: Current FSM state
        db_session: Database session

    Workflow:
        1. Validate input format
        2. Check gift availability
        3. Process payment (balance or invoice)
        4. Handle success/error cases
    """
    if message.text == "🔙 Back":
        await return_to_main_menu(message, state)
        return

    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.reply("Enter gift ID, recipient ID and quantity separated by spaces.")
            return

        try:
            gift_id, user_id, gifts_count = map(int, parts)
        except ValueError:
            await message.reply("All values must be numbers.")
            return

        payload = f"gift_{gift_id}_to_{user_id}_count_{gifts_count}"

        gifts_list = await fetch_gifts_list()
        gift_price = next(
            (gift["star_count"] for gift in gifts_list if int(gift["id"]) == gift_id), None)
        if gift_price is None:
            await message.reply("Gift with specified ID not found.")
            return

        amount = gift_price * gifts_count

        with db_session as db:
            user = db.query(User).filter(
                User.user_id == message.from_user.id).first()
            if not user:
                await message.reply("User not found.")
                return

            if user.balance >= amount:
                user.balance -= amount

                transaction = Transaction(
                    user_id=user.user_id,
                    amount=amount,
                    telegram_payment_charge_id="local_transaction",
                    status="completed",
                    time=datetime.now().isoformat(),
                    payload=payload  # Store payload
                )
                db.add(transaction)
                db.commit()

                await message.reply(f"Purchase successful! Remaining balance: {user.balance}⭐️.")
                await process_gift_payment(message=message, db_session=db_session, from_balance=True)
            else:
                required_amount = amount - user.balance
                prices = [types.LabeledPrice(
                    label="Additional deposit", amount=required_amount)]
                await message.answer_invoice(
                    title="Additional deposit",
                    description=f"Purchase requires {amount}⭐️, you have {user.balance}⭐️.",
                    payload=payload,  # Pass payload
                    currency="XTR",
                    prices=prices,
                    provider_token="",
                    reply_markup=payment_keyboard(price=required_amount)
                )
                await state.clear()

    except Exception as e:
        log.error(f"Error: {e}")
        await message.reply("An error occurred. Please try again.")
