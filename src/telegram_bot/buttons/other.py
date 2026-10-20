from aiogram.types import InlineKeyboardButton

# TODO: тут можно добавить параметр disabled
admin_menu_b = InlineKeyboardButton(text="🏜️ Меню админа", callback_data="admin_menu")
student_settings_b = InlineKeyboardButton(text="⚙️ Настройки", callback_data="student_settings")


def back_b(inline_button: InlineKeyboardButton) -> InlineKeyboardButton:
    return InlineKeyboardButton(text="◀️ Назад", callback_data=inline_button.callback_data)
