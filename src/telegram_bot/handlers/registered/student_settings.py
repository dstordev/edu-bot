from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, User
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, Checkbox, ManagedCheckbox
from aiogram_dialog.widgets.text import Const
from loguru import logger

from db.repositories import DBRepositories
from telegram_bot.buttons.other import student_settings_b
from telegram_bot.handlers.registered.general import command_start_handler_registered
from telegram_bot.utils.html_format import b, i


class StudentSettingsSG(StatesGroup):
    main = State()


student_settings_router = Router(name=__name__)


@student_settings_router.callback_query(F.data == student_settings_b.callback_data)
async def student_settings_menu(callback: CallbackQuery, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(StudentSettingsSG.main, mode=StartMode.RESET_STACK)


async def on_dialog_start(start_data: dict | None, manager: DialogManager) -> None:
    repos: DBRepositories = manager.middleware_data["dbrepositories"]
    user: User | None = manager.middleware_data.get("event_from_user") or manager.event.from_user

    if not user:
        logger.error("Не удалось определить пользователя при открытии настроек")
        return

    student = await repos.student.find_by_telegram_id(user.id)
    if not student:
        logger.warning(f"Студент {user.id} не найден в БД")
        return

    student_settings = await repos.student_settings.find(student.id)
    if not student_settings:
        logger.warning(f"Настройки для студента {student.id} не найдены")
        return

    manager.dialog_data["student_id"] = student.id

    checkbox: ManagedCheckbox | None = manager.find("reminder_5min_checkbox")
    if checkbox:
        await checkbox.set_checked(student_settings.reminder_5min)


async def on_reminder_5min_toggled(
    callback: CallbackQuery,
    checkbox: ManagedCheckbox,
    manager: DialogManager,
) -> None:
    student_id = manager.dialog_data.get("student_id")
    if not student_id:
        logger.warning("Студент не найден в dialog_data при переключении настройки")
        await callback.answer("Ошибка сохранения данных", show_alert=True)
        return

    is_checked = not checkbox.is_checked()

    repos: DBRepositories = manager.middleware_data["dbrepositories"]
    await repos.student_settings.set_reminder_5min(student_id, is_checked)

    msg = "🔔 Напоминания включены" if is_checked else "🔕 Напоминания отключены"
    await callback.answer(msg)


async def on_back_to_menu(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
) -> None:
    state = manager.middleware_data["state"]
    await command_start_handler_registered(callback, state, manager)


student_settings_dialog = Dialog(
    Window(
        Const(f"{b('⚙️ Настройки')}\n{i('Тут ты можешь настроить что-то под себя.')}"),
        Checkbox(
            checked_text=Const("🔔 Напоминание о паре за 5 мин."),
            unchecked_text=Const("🔕 Напоминание о паре за 5 мин."),
            id="reminder_5min_checkbox",
            on_click=on_reminder_5min_toggled,
        ),
        Button(
            Const("◀️ Назад"),
            id="back_to_menu",
            on_click=on_back_to_menu,
        ),
        state=StudentSettingsSG.main,
    ),
    on_start=on_dialog_start,
)

student_settings_router.include_router(student_settings_dialog)
