from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Row
from aiogram_dialog.widgets.text import Const

cancel_button = Cancel(Const("⏪ Назад"))
back_button = Back(Const("◀️ Назад"))


def confirmation_row(on_confirm, confirm_id: str = "confirm"):
    return Row(
        Button(Const("✅ Подтвердить"), id=confirm_id, on_click=on_confirm),
        Cancel(Const("❌ Отмена")),
    )
