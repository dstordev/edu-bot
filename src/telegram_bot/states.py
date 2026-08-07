from aiogram.fsm.state import State, StatesGroup


class StartForm(StatesGroup):
    full_name = State()  # Состояние ожидания ввода ФИО
    group = State()  # Состояние ожидания ввода группы


class AddHomeworkForm(StatesGroup):
    academic_subject = State()
    text = State()
    file_or_photo = State()
    assignment_date = State()
    confirm = State()
