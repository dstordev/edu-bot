from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models.tables import Group
from telegram_bot.buttons.unregistered import group_button
from telegram_bot.utils.html_format import b
from telegram_bot.windows.info_window import InfoWindow


def wait_full_name_window():
    return InfoWindow(b("✏️ Введите свои ФИО или ФИ:"))


def wait_group_window(groups: list[Group]):
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.add(group_button(group_name=group.name, group_id=group.id))
    builder.adjust(1)

    return InfoWindow(b("✏️ Выберите свою группу ниже:"), builder.as_markup())


def not_found_groups_window():
    return InfoWindow(b("🐱 Группы еще не указаны, вернитесь немного позже"))
