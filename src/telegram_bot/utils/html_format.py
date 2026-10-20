from typing import Any


def b(text: Any) -> str:
    return "<b>" + str(text) + "</b>"


def code(text: Any) -> str:
    return "<code>" + str(text) + "</code>"


def i(text: Any) -> str:
    return "<i>" + str(text) + "</i>"


def blockquote(text: Any) -> str:
    return "<blockquote>" + str(text) + "</blockquote>"
