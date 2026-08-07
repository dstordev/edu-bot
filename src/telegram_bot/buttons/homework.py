from typing import Literal

from aiogram.enums.button_style import ButtonStyle
from aiogram.types import InlineKeyboardButton

from db.models.tables import AcademicSubject

homework_menu_b = InlineKeyboardButton(
    text="📙 Домашние задания", callback_data="homework_menu", style=ButtonStyle.PRIMARY
)
homework_add_b = InlineKeyboardButton(text="➕ Добавить", callback_data="homework:add")


def homework_unfinished_b(page_index: int = 0):
    return InlineKeyboardButton(
        text="🟠 Невыполненное",
        callback_data=f"homework_view:unfinished:page:{page_index}",
    )


def homework_finished_b(page_index: int = 0):
    return InlineKeyboardButton(
        text="🟢 Выполненное", callback_data=f"homework_view:finished:page:{page_index}"
    )


def complete_homework_b(homework_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="✅ Выполнить",
        callback_data=f"complete_homework:{homework_id}",
        style=ButtonStyle.SUCCESS,
    )


def homework_b(
    *, homework_id: int, homework_academic_subject: AcademicSubject
) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=f"{homework_id} | {homework_academic_subject.name}",
        callback_data=f"homework:{homework_id}",
    )


def homework_next_page_b(
    *, htype: Literal["unfinished", "finished"], page_index: int
) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="➡️", callback_data=f"homework_view:{htype}:page:{page_index}"
    )


def homework_previous_page_b(
    *, htype: Literal["unfinished", "finished"], page_index: int
) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="⬅️", callback_data=f"homework_view:{htype}:page:{page_index}"
    )


def view_homework_files_b(homework_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="Показать все материалы",
        callback_data=f"view_homework_files:{homework_id}",
    )
