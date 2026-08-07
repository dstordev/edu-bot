from typing import Any


def b(text: Any):
    return "<b>" + str(text) + "</b>"


def code(text: Any):
    return "<code>" + str(text) + "</code>"


def i(text: Any):
    return "<i>" + str(text) + "</i>"


def blockquote(text: Any):
    return "<blockquote>" + str(text) + "</blockquote>"
