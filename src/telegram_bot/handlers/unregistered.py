from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from db.repositories import DBRepositories
from settings import settings
from telegram_bot.buttons.other import start_b
from telegram_bot.states import StartForm
from telegram_bot.utils.html_format import b
from telegram_bot.windows.registered import start_window
from telegram_bot.windows.unregistered import (
    not_found_groups_window,
    wait_full_name_window,
    wait_group_window,
)

unregistered_router = Router(name=__name__)


@unregistered_router.message(CommandStart())
@unregistered_router.callback_query(F.data == start_b.callback_data)
async def command_start_handler(
    event: Message | CallbackQuery, state: FSMContext, dbrepositories: DBRepositories
) -> None:
    groups = await dbrepositories.group.get_groups()

    if len(groups) == 0:
        await not_found_groups_window().answer_window(event)
        return

    await state.set_state(StartForm.group)
    # TODO: Отправлять окно о том, что нужно ввести токен группы а не выбирать ее
    await wait_group_window().answer_window(event)


@unregistered_router.message(StartForm.group, F.text)
async def group_selection_handler(
    event: Message, state: FSMContext, dbrepositories: DBRepositories
):
    token: str = event.text.strip()  # pyright: ignore[reportOptionalMemberAccess]

    if (group := await dbrepositories.group.find_by_token(token)) is None:
        return await event.answer(
            b("😿 Такого токена не существует, перепроверьте правильность набора")
        )

    await state.set_data({"group_id": group.id})
    await state.set_state(StartForm.full_name)
    await wait_full_name_window().answer_window(event)


@unregistered_router.message(StartForm.full_name, F.text)
async def message_full_name_handler(
    event: Message, state: FSMContext, bot: Bot, dbrepositories: DBRepositories
):
    if not event.from_user:
        return logger.warning("Полученное сообщение ожидается от пользователя.")

    full_name: str = event.text  # pyright: ignore[reportAssignmentType]

    # Нормализуем ввод: удаляем лишние пробелы и обрезаем знаки пунктуации
    parts = [p.strip(" ,;.\t\n\r") for p in full_name.strip().split() if p.strip()]

    # Ожидаем минимум: фамилия и имя (2 слова). Если меньше — просим ввести снова.
    if len(parts) < 2:
        return await event.answer(
            "⚠️ Введите ФИО или ФИ (например: Иванов Иван Иванович или Иванов Иван). Попробуйте ещё раз:"
        )

    # Если ровно 2 слова — считаем это ФИ (фамилия, имя).
    if len(parts) == 2:
        surname, name = parts[0], parts[1]
        patronymic = ""
    else:
        # 3 или более слов — первая часть считается фамилией, вторая — именем,
        # остальные части объединяем в отчество (поддерживает двойные отчества).
        surname = parts[0]
        name = parts[1]
        patronymic = " ".join(parts[2:])

    group_id = (await state.get_data())["group_id"]

    await dbrepositories.student.create(
        telegram_id=event.from_user.id,
        surname=surname,
        name=name,
        patronymic=patronymic,
        group_id=group_id,
    )

    await state.clear()
    await event.answer(b("😸 Успешно вас зарегестрировал!"))
    # Уведомляем админа
    for admin_id in settings.ADMIN_IDS:
        await bot.send_message(admin_id, "😸 Зарегестрирован новый пользователь!")
    return await start_window().answer_window(event)
