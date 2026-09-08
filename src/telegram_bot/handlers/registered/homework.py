from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaUnion,
)

from db.repositories import DBRepositories
from telegram_bot.buttons.homework import (
    homework_finished_b,
    homework_menu_b,
    homework_unfinished_b,
)
from telegram_bot.utils.html_format import b
from telegram_bot.windows.homework import (
    finished_homework_window,
    homework_menu_window,
    homework_window,
    unfinished_homework_window,
)

registered_homework_router = Router(name=__name__)


@registered_homework_router.callback_query(F.data == homework_menu_b.callback_data)
async def handler_homework_menu(event: CallbackQuery):
    await homework_menu_window().answer_window(event)


@registered_homework_router.callback_query(
    F.data.startswith("homework_view:unfinished:page:")
)
async def handler_homework_unfinished(
    event: CallbackQuery, dbrepositories: DBRepositories, state: FSMContext
):
    page_index: int = int(event.data.split(":")[3])  # pyright: ignore[reportOptionalMemberAccess]

    user_id = event.from_user.id

    student = await dbrepositories.student.find_by_telegram_id(user_id)
    assert student is not None

    unfinished_homeworks = await dbrepositories.homework.get_unfinished_homeworks(
        student.id, student.group_id, page_index=page_index
    )

    if len(unfinished_homeworks) == 0:
        await event.answer("🐈 Здесь нет невыполненных заданий", show_alert=True)
        return

    await state.update_data({"homework_view:unfinished:page": page_index})

    await unfinished_homework_window(
        homeworks=list(unfinished_homeworks),
        back_btn=homework_menu_b,
        page_index=page_index,
    ).answer_window(event)


@registered_homework_router.callback_query(
    F.data.startswith("homework_view:finished:page:")
)
async def handler_homework_finished(
    event: CallbackQuery, dbrepositories: DBRepositories, state: FSMContext
):
    page_index: int = int(event.data.split(":")[3])  # pyright: ignore[reportOptionalMemberAccess]

    user_id = event.from_user.id

    student = await dbrepositories.student.find_by_telegram_id(user_id)
    assert student is not None

    finished_homeworks = await dbrepositories.homework.get_finished_homeworks(
        student.id, page_index=page_index
    )

    if len(finished_homeworks) == 0:
        await event.answer("🐈 Здесь нет выполненных заданий", show_alert=True)
        return

    await state.update_data({"homework_view:finished:page": page_index})

    await finished_homework_window(
        homeworks=list(finished_homeworks),
        back_btn=homework_menu_b,
        page_index=page_index,
    ).answer_window(event)


@registered_homework_router.callback_query(F.data.startswith("homework:"))
async def handler_homework(
    event: CallbackQuery, dbrepositories: DBRepositories, state: FSMContext
):
    homework_id = int(event.data.split(":")[1])  # pyright: ignore[reportOptionalMemberAccess]

    user_id = event.from_user.id

    student = await dbrepositories.student.find_by_telegram_id(user_id)
    assert student is not None

    homework = await dbrepositories.homework.get_homework(homework_id)
    assert homework is not None

    homework_finished = await dbrepositories.homework.is_finished_homework(
        student_id=student.id, homework_id=homework_id
    )

    media: InputMediaUnion | None = None
    if len(homework.homework_photo) > 0:
        media = InputMediaPhoto(media=homework.homework_photo[0].telegram_file_id)
    elif len(homework.homework_file) > 0:
        media = InputMediaDocument(media=homework.homework_file[0].telegram_file_id)

    if not homework_finished:
        page_index: int = 0
        if _page_index := await state.get_value("homework_view:unfinished:page"):
            page_index = _page_index

        back_btn = homework_unfinished_b(page_index)
        cmplt_btn = True
    else:
        page_index: int = 0
        if _page_index := await state.get_value("homework_view:finished:page"):
            page_index = _page_index

        back_btn = homework_finished_b(page_index)
        cmplt_btn = False

    await homework_window(
        homework=homework,
        back_btn=back_btn,
        cmplt_btn=cmplt_btn,
        media=media,
        additional_material_btn=(
            len(homework.homework_file) + len(homework.homework_photo)
        )
        > 1,
    ).answer_window(event)


@registered_homework_router.callback_query(F.data.startswith("complete_homework:"))
async def handler_complete_homework(
    event: CallbackQuery, dbrepositories: DBRepositories
):
    homework_id = int(event.data.split(":")[1])  # pyright: ignore[reportOptionalMemberAccess]

    user_id = event.from_user.id

    student = await dbrepositories.student.find_by_telegram_id(user_id)
    assert student is not None
    await dbrepositories.student_homework.mark_completed(
        student_id=student.id, homework_id=homework_id
    )

    await event.answer("✅ Отметил домашнее задание как выполненное", show_alert=True)

    await handler_homework_menu(event)


@registered_homework_router.callback_query(F.data.startswith("view_homework_files:"))
async def handler_view_homework_files(
    event: CallbackQuery, dbrepositories: DBRepositories
):
    homework_id = int(event.data.split(":")[1])  # pyright: ignore[reportOptionalMemberAccess]

    homework = await dbrepositories.homework.get_homework(homework_id)
    assert homework is not None

    photo_media_group: list[InputMediaPhoto] = [
        InputMediaPhoto(media=i.telegram_file_id) for i in homework.homework_photo
    ]
    if len(photo_media_group) > 0:
        photo_media_group[0].caption = b(
            f"📑 Материал к домашнему заданию {homework.id}"
        )
        await event.message.answer_media_group(list(photo_media_group))  # pyright: ignore[reportOptionalMemberAccess]

    files_media_group: list[InputMediaDocument] = [
        InputMediaDocument(media=i.telegram_file_id) for i in homework.homework_file
    ]
    if len(files_media_group) > 0:
        files_media_group[-1].caption = b(
            f"📑 Материал к домашнему заданию {homework.id}"
        )
        await event.message.answer_media_group(list(files_media_group))  # pyright: ignore[reportOptionalMemberAccess]
