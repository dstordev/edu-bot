from aiogram.types import InlineKeyboardButton


def back_b(inline_button: InlineKeyboardButton) -> InlineKeyboardButton:
    return InlineKeyboardButton(text="◀️ Назад", callback_data=inline_button.callback_data)
