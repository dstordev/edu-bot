from typing import Any

from aiogram_dialog import DialogManager


async def getter_group_token(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    return {"has_error": dialog_manager.dialog_data.get("token_not_found", False)}


async def getter_student_name(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    return {"has_error": dialog_manager.dialog_data.get("bad_student_name", False)}
