from aiogram.enums.button_style import ButtonStyle
from aiogram.types import InlineKeyboardButton

from db.models.tables import AcademicSubject

homework_menu_b = InlineKeyboardButton(
    text="📙 Домашние задания", callback_data="homework_menu", style=ButtonStyle.PRIMARY
)


def homework_unfinished_b(page_index: int = 0) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="🟠 Невыполненное",
        callback_data=f"homework_view:unfinished:page:{page_index}",
    )


def homework_finished_b(page_index: int = 0) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="🟢 Выполненное", callback_data=f"homework_view:finished:page:{page_index}"
    )


def homework_b(
    *, homework_id: int, homework_academic_subject: AcademicSubject
) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=f"{homework_id} | {homework_academic_subject.name}",
        callback_data=f"homework:{homework_id}",
    )
