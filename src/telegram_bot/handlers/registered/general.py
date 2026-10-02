from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from settings import settings
from telegram_bot.buttons.other import start_b
from telegram_bot.windows.registered import start_window

registered_general_router = Router(name=__name__)


@registered_general_router.message(CommandStart())
@registered_general_router.callback_query(F.data == start_b.callback_data)
async def command_start_handler_registered(
    event: Message | CallbackQuery, state: FSMContext
) -> None:
    # Чтобы избежать предупреждений pyright и ruff
    if not event.from_user:
        return
    await state.clear()
    await start_window(event.from_user.id in settings.ADMIN_IDS).answer_window(event)
