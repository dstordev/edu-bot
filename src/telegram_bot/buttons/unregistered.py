from aiogram.types import InlineKeyboardButton


def group_button(group_name: str, group_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=group_name, callback_data=f"group_id:{group_id}")
