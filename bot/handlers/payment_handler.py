from aiogram import types, Router, F

from utils.logger import log
from bot.handlers.balance import process_deposit_payment
from bot.handlers.buy_gift import process_gift_payment


router = Router()


@log.catch
@router.message(F.successful_payment)
async def handle_successful_payment(message: types.Message, db_session):
    """
    Universal handler for successful payments.

    Processes different payment types based on payload prefix:
    - 'deposit_' prefix: handles deposit payments
    - 'gift_' prefix: handles gift payments

    Args:
        message: The message object containing payment info
        db_session: Database session for transaction processing

    Logs:
        - Successful payment details
        - Unknown payment type errors

    Responses:
        - Routes to appropriate payment handler
        - Error message for unknown payment types
    """
    payment_info = message.successful_payment
    log.info(f"Successful payment: {payment_info}")

    payload = payment_info.invoice_payload

    # Determine payment type by payload prefix
    if payload.startswith("deposit_"):
        await process_deposit_payment(message, db_session, payment_info)
    elif payload.startswith("gift_"):
        await process_gift_payment(message, db_session, payment_info)
    else:
        log.error(f"Unknown payment type: {payload}")
        await message.reply("Error: Unknown payment type. Please contact support.")
