from datetime import date, datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from db.repositories import DBRepositories
from telegram_bot.buttons.homework import homework_add_b, homework_menu_b
from telegram_bot.buttons.other import cancel_b, confirm_b, skip_b
from telegram_bot.states import AddHomeworkForm
from telegram_bot.utils.html_format import b
from telegram_bot.windows.homework import (
    file_or_photo_window,
    homework_assignment_date_window,
    homework_confirm_window,
    homework_created_window,
    homework_menu_window,
    text_homework_window,
)
from telegram_bot.windows.registered import academic_subjects_window, start_window
from utils.datetime_format import DATE_FORMAT

admin_homework_router = Router()


@admin_homework_router.callback_query(F.data == homework_menu_b.callback_data)
async def handler_homework_menu(event: CallbackQuery):
    await homework_menu_window(add_btn=True).answer_window(event)


@admin_homework_router.callback_query(F.data == homework_add_b.callback_data)
async def handler_homework_add(
    event: CallbackQuery, dbrepositories: DBRepositories, state: FSMContext
):
    await state.clear()

    academic_subjects = await dbrepositories.academic_subject.get_all(limit=20)

    await state.set_state(AddHomeworkForm.academic_subject)
    await academic_subjects_window(
        academic_subjects=list(academic_subjects), back_btn=homework_menu_b
    ).answer_window(event)


@admin_homework_router.callback_query(
    F.data.startswith("academic_subject:"), AddHomeworkForm.academic_subject
)
async def handler_academic_subject_id(event: CallbackQuery, state: FSMContext):
    # вытаскиваем выбранный academic subject id
    academic_subject_id = int(event.data.split(":")[1])  # pyright: ignore[reportOptionalMemberAccess]

    # запоминаем academic subject
    await state.update_data({"academic_subject_id": academic_subject_id})

    # переходим на следующий этап заполнения домашнего задания
    await state.set_state(AddHomeworkForm.text)
    await text_homework_window(back_btn=homework_add_b).answer_window(event)


@admin_homework_router.message(F.text, AddHomeworkForm.text)
async def handler_homework_text(event: Message, state: FSMContext):
    assert event.text

    # запоминаем введенный текст
    await state.update_data({"text": event.text})

    # переходим на следующий этап заполнения домашнего задания
    await state.set_state(AddHomeworkForm.file_or_photo)
    await file_or_photo_window(back_btn=homework_add_b).answer_window(event)


### Обработчик сообщения с фотографией
@admin_homework_router.message(
    F.photo, ~F.media_group_id, AddHomeworkForm.file_or_photo
)
async def handler_file_or_photo_photo(event: Message, state: FSMContext):
    assert event.photo is not None
    file_id = event.photo[-1].file_id

    photo_file_ids: list[str] | None = await state.get_value("photo_file_ids")
    if photo_file_ids is None:
        photo_file_ids = []
    if file_id not in photo_file_ids:
        photo_file_ids.append(file_id)
    else:
        print("файл уже есть")

    await state.update_data({"photo_file_ids": photo_file_ids})
    await event.answer(
        b(
            "Успешно прикрепил изображение, можете пропустить или добавить ещё изображение"
        )
    )
    # переходим на следующий этап заполнения домашнего задания
    await file_or_photo_window(back_btn=homework_add_b).answer_window(event)


### Обработчик сообщения с фотографией
@admin_homework_router.message(
    F.document, ~F.media_group_id, AddHomeworkForm.file_or_photo
)
async def handler_file_or_photo_file(event: Message, state: FSMContext):
    assert event.document is not None
    file_id = event.document.file_id

    file_file_ids: list[str] | None = await state.get_value("file_file_ids")
    if file_file_ids is None:
        file_file_ids = []
    if file_id not in file_file_ids:
        file_file_ids.append(file_id)
    else:
        print("файл уже есть")

    await state.update_data({"file_file_ids": file_file_ids})
    await event.answer(
        b("Успешно прикрепил файл, можете пропустить или добавить ещё файл")
    )
    # переходим на следующий этап заполнения домашнего задания
    await file_or_photo_window(back_btn=homework_add_b).answer_window(event)


@admin_homework_router.callback_query(
    F.data == skip_b.callback_data, AddHomeworkForm.file_or_photo
)
async def handler_file_or_photo_skip(event: CallbackQuery, state: FSMContext):
    await state.set_state(AddHomeworkForm.assignment_date)

    # переходим на следующий этап заполнения домашнего задания
    await homework_assignment_date_window(back_btn=homework_add_b).answer_window(event)


@admin_homework_router.callback_query(
    F.data == skip_b.callback_data, AddHomeworkForm.assignment_date
)
async def handler_assignment_date_skip(
    event: CallbackQuery, dbrepositories: DBRepositories, state: FSMContext
):
    await state.set_state(AddHomeworkForm.confirm)

    academic_subject_id: int | None = await state.get_value("academic_subject_id")
    assert academic_subject_id is not None

    academic_subject = await dbrepositories.academic_subject.get_by_id(
        academic_subject_id
    )
    assert academic_subject

    text: str | None = await state.get_value("text")
    assert text is not None

    assignment_date: date | None = await state.get_value("assignment_date")

    # переходим на следующий этап заполнения домашнего задания
    await homework_confirm_window(
        academic_subject=academic_subject, text=text, assignment_date=assignment_date
    ).answer_window(event)


### Обработчик ввода даты назначения ДЗ
@admin_homework_router.message(F.text, AddHomeworkForm.assignment_date)
async def handler_assignment_date(
    event: Message, dbrepositories: DBRepositories, state: FSMContext
):
    try:
        assignment_date: date = datetime.strptime(event.text, DATE_FORMAT).date()  # pyright: ignore[reportArgumentType]
    except ValueError:
        logger.warning("Не удалось преобразовать дату назначения домашнего задания")
        await homework_assignment_date_window(back_btn=homework_add_b).answer_window(
            event
        )
        return

    await state.update_data({"assignment_date": event.text})

    academic_subject_id: int | None = await state.get_value("academic_subject_id")
    assert academic_subject_id is not None

    academic_subject = await dbrepositories.academic_subject.get_by_id(
        academic_subject_id
    )
    assert academic_subject

    text: str | None = await state.get_value("text")
    assert text is not None

    await state.set_state(AddHomeworkForm.confirm)

    # переходим на следующий этап заполнения домашнего задания
    await homework_confirm_window(
        academic_subject=academic_subject, text=text, assignment_date=assignment_date
    ).answer_window(event)


### Обработчик подтверждения создания ДЗ
@admin_homework_router.callback_query(
    F.data.in_([confirm_b.callback_data, cancel_b.callback_data]),
    AddHomeworkForm.confirm,
)
async def handler_homework_confirm(
    event: CallbackQuery, dbrepositories: DBRepositories, state: FSMContext
):
    is_confirm: bool = event.data == confirm_b.callback_data

    if is_confirm is False:
        await state.clear()
        await start_window().answer_window(event)
        return

    academic_subject_id: int | None = await state.get_value("academic_subject_id")
    assert academic_subject_id is not None

    text: str | None = await state.get_value("text")
    assert text is not None

    assignment_date: date | None = None
    _assignment_date: str | None = await state.get_value("assignment_date")
    if _assignment_date:
        assignment_date = datetime.strptime(_assignment_date, DATE_FORMAT).date()

    file_file_ids: list[str] | None = await state.get_value("file_file_ids")
    photo_file_ids: list[str] | None = await state.get_value("photo_file_ids")

    try:
        await dbrepositories.homework.add_homework(
            academic_subject_id=academic_subject_id,
            text=text,
            assignment_date=assignment_date,
            photo_telegram_file_ids=photo_file_ids,
            file_telegram_file_ids=file_file_ids,
        )
    except Exception as ex:
        logger.error("Не удалось создать домашнее задание.")
        raise ex

    await state.clear()
    await homework_created_window().answer_window(event)
