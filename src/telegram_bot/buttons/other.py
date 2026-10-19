from aiogram.types import InlineKeyboardButton, WebAppInfo

# TODO: Сделать функцию, которая принимает URL сайта?
ranepa_b = InlineKeyboardButton(
    text="🌐 Сайт РАНХиГС", web_app=WebAppInfo(url="https://my.ranepa.ru/lk/student")
)

start_b = InlineKeyboardButton(text="⏪ Главное меню", callback_data="start")

# TODO: тут можно добавить параметр disabled
empty_b = InlineKeyboardButton(text="", callback_data="_")
admin_menu_b = InlineKeyboardButton(text="🏜️ Меню админа", callback_data="admin_menu")
student_settings_b = InlineKeyboardButton(
    text="⚙️ Настройки", callback_data="student_settings"
)


def back_b(inline_button: InlineKeyboardButton) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="◀️ Назад", callback_data=inline_button.callback_data
    )


def academic_subject_b(*, name: str, academic_subject_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=name, callback_data=f"academic_subject:{academic_subject_id}"
    )
