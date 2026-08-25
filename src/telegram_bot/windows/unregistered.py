from telegram_bot.utils.html_format import b
from telegram_bot.windows.info_window import InfoWindow


def wait_full_name_window():
    return InfoWindow(b("✏️ Введите свои ФИО или ФИ:"))


def wait_group_window():
    return InfoWindow(b("✏️ Введите код доступа к своей группе ниже:"))


def not_found_groups_window():
    return InfoWindow(b("🐱 Группы еще не указаны, вернитесь немного позже"))
