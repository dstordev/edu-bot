from aiogram.types import InlineKeyboardButton, InputMediaUnion
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models.tables import Homework
from telegram_bot.buttons.homework import (
    complete_homework_b,
    homework_b,
    homework_finished_b,
    homework_menu_b,
    homework_next_page_b,
    homework_previous_page_b,
    homework_unfinished_b,
    view_homework_files_b,
)
from telegram_bot.buttons.other import back_b, empty_b, start_b
from telegram_bot.utils.html_format import b, blockquote
from telegram_bot.windows.info_window import InfoWindow
from utils.datetime_format import DATE_FORMAT


def homework_menu_window():
    builder = InlineKeyboardBuilder()
    builder.add(homework_unfinished_b(), homework_finished_b(), start_b)
    builder.adjust(1)

    return InfoWindow(b(homework_menu_b.text), builder.as_markup())


def unfinished_homework_window(
    *, homeworks: list[Homework], back_btn: InlineKeyboardButton, page_index: int
):
    builder = InlineKeyboardBuilder()

    # добавляем дзшки в кнопки
    for homework in homeworks:
        builder.add(
            homework_b(
                homework_id=homework.id,
                homework_academic_subject=homework.academic_subject,
            )
        )
    if page_index > 0:
        builder.add(homework_previous_page_b(htype="unfinished", page_index=page_index - 1))
    else:
        builder.add(empty_b)
    builder.add(homework_next_page_b(htype="unfinished", page_index=page_index + 1))
    builder.add(back_b(back_btn))
    builder.adjust(*([1] * len(homeworks)), 2, 1)

    return InfoWindow(
        b("🟠 Ваши невыполненные задания:"), inline_keyboard_markup=builder.as_markup()
    )


def finished_homework_window(
    *, homeworks: list[Homework], back_btn: InlineKeyboardButton, page_index: int
):
    builder = InlineKeyboardBuilder()

    # добавляем дзшки в кнопки
    for homework in homeworks:
        builder.add(
            homework_b(
                homework_id=homework.id,
                homework_academic_subject=homework.academic_subject,
            )
        )
    if page_index > 0:
        builder.add(homework_previous_page_b(htype="finished", page_index=page_index - 1))
    else:
        builder.add(empty_b)
    builder.add(homework_next_page_b(htype="finished", page_index=page_index + 1))
    builder.add(back_b(back_btn))
    builder.adjust(*[1 for _ in range(len(homeworks))], 2, 1)

    return InfoWindow(b("🟢 Ваши выполненные задания:"), inline_keyboard_markup=builder.as_markup())


def homework_window(
    *,
    homework: Homework,
    back_btn: InlineKeyboardButton,
    cmplt_btn: bool = False,
    additional_material_btn: bool = False,
    media: InputMediaUnion | None = None,
):
    builder = InlineKeyboardBuilder()
    if additional_material_btn:
        builder.add(view_homework_files_b(homework.id))
    if cmplt_btn:
        builder.add(complete_homework_b(homework.id))
    builder.add(back_b(back_btn))
    builder.adjust(1)

    message_text = f"{b('📌 Домашнее задание')}\n"
    if homework.assignment_date:
        message_text += f"— Дата назначения: {format(homework.assignment_date, DATE_FORMAT)}\n"
    message_text += f"— Предмет: {homework.academic_subject.name}\n\n{blockquote(homework.text)}"

    return InfoWindow(message_text, builder.as_markup(), media=media)
