from aiogram.enums import ButtonStyle
from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Column, Start, WebApp
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format

from metadata import VERSION
from settings import settings
from telegram_bot.handlers.admin.states import AdminMenuSG
from telegram_bot.handlers.registered.homework import HomeworkSG
from telegram_bot.handlers.registered.schedule import ScheduleSG
from telegram_bot.handlers.registered.student_settings import StudentSettingsSG
from telegram_bot.utils.html_format import b, blockquote


class MainMenuSG(StatesGroup):
    main = State()


async def get_main_menu_data(dialog_manager: DialogManager, **kwargs: dict) -> dict:
    user = dialog_manager.event.from_user
    is_admin = user.id in settings.ADMIN_IDS if user else False
    return {"is_admin": is_admin}


main_menu_dialog = Dialog(
    Window(
        Format(b("😼 Учебный помощник\n") + blockquote(f"Версия: v{VERSION}")),
        Column(
            Start(
                Const("🗓️ Расписание"),
                id="to_schedule",
                state=ScheduleSG.main,
                style=Style(style=ButtonStyle.PRIMARY),
            ),
            Start(
                Const("📙 Домашние задания"),
                id="to_homework",
                state=HomeworkSG.menu,
                style=Style(style=ButtonStyle.PRIMARY),
            ),
            WebApp(
                text=Const("🌐 Сайт РАНХиГС"),
                url=Const("https://my.ranepa.ru/lk/student"),
            ),
            Start(
                Const("⚙️ Настройки"),
                id="to_settings",
                state=StudentSettingsSG.main,
            ),
            # Кнопка покажется ТОЛЬКО админу:
            Start(
                Const("🏜️ Меню админа"),
                id="to_admin",
                state=AdminMenuSG.main,
                when="is_admin",
            ),
        ),
        state=MainMenuSG.main,
        getter=get_main_menu_data,
    )
)
