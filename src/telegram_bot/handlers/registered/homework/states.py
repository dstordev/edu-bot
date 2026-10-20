from aiogram.fsm.state import State, StatesGroup


class HomeworkSG(StatesGroup):
    menu = State()  # Меню выбора: выполненные / невыполненные
    list = State()  # Универсальный список заданий с пагинацией
    detail = State()  # Просмотр конкретного задания
