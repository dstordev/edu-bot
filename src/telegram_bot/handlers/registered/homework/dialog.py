from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Column, Row, Select, SwitchTo
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from telegram_bot.buttons.homework import (
    homework_finished_b,
    homework_menu_b,
    homework_unfinished_b,
)
from telegram_bot.utils.html_format import b

from .getters import get_homework_detail_data, get_homework_list_data
from .handlers import (
    on_change_page,
    on_complete_homework,
    on_homework_select,
    on_open_list,
    on_view_files,
)
from .states import HomeworkSG

homework_dialog = Dialog(
    # 1. Меню ДЗ
    Window(
        Const(b(homework_menu_b.text)),
        Button(
            Const(homework_unfinished_b().text),
            id="unfinished",
            on_click=on_open_list,
        ),
        Button(
            Const(homework_finished_b().text),
            id="finished",
            on_click=on_open_list,
        ),
        Cancel(Const("◀️ Главное меню")),
        state=HomeworkSG.menu,
    ),
    # 2. Список заданий
    Window(
        Format("{list_title}"),
        Column(
            Select(
                Format("{item[title]}"),
                id="select_hw",
                item_id_getter=lambda item: item["id"],
                items="homeworks",
                on_click=on_homework_select,
            )
        ),
        Row(
            Button(
                Const("⬅️ Предыдущая"),
                id="prev_page",
                on_click=on_change_page,
                when="has_prev",
            ),
            Button(
                Const("Следующая ➡️"),
                id="next_page",
                on_click=on_change_page,
            ),
        ),
        SwitchTo(Const("◀️ Назад"), id="back_to_menu", state=HomeworkSG.menu),
        state=HomeworkSG.list,
        getter=get_homework_list_data,
    ),
    # 3. Детальный просмотр задания
    Window(
        DynamicMedia("media", when="has_media"),
        Format("{detail_text}"),
        Button(
            Const("📑 Материалы к заданию"),
            id="view_files",
            on_click=on_view_files,
            when="has_additional_material",
        ),
        Button(
            Const("✅ Отметить выполненным"),
            id="complete_hw",
            on_click=on_complete_homework,
            when="can_complete",
        ),
        SwitchTo(Const("◀️ Назад"), id="back_to_list", state=HomeworkSG.list),
        state=HomeworkSG.detail,
        getter=get_homework_detail_data,
    ),
)
