from aiogram.types import InlineKeyboardButton, WebAppInfo

# TODO: Сделать функцию, которая принимает URL сайта?
ranepa_b = InlineKeyboardButton(
    text="🌐 Сайт РАНХиГС", web_app=WebAppInfo(url="https://my.ranepa.ru/lk/student")
)

start_b = InlineKeyboardButton(text="⏪ Главное меню", callback_data="start")

images_b = InlineKeyboardButton(text="🖼 Изображения", callback_data="images")

files_b = InlineKeyboardButton(text="📁 Файлы", callback_data="files")

skip_b = InlineKeyboardButton(text="▶️ Пропустить", callback_data="skip")

confirm_b = InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm")
cancel_b = InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")

empty_b = InlineKeyboardButton(text="", callback_data="_")


def back_b(inline_button: InlineKeyboardButton) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="◀️ Назад", callback_data=inline_button.callback_data
    )


def academic_subject_b(*, name: str, academic_subject_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=name, callback_data=f"academic_subject:{academic_subject_id}"
    )
