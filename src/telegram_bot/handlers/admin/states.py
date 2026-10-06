from aiogram.fsm.state import State, StatesGroup


class AdminMenuSG(StatesGroup):
    main = State()


class AddHomeworkSG(StatesGroup):
    academic_subject = State()
    text = State()
    photo_or_document = State()
    assignment_date = State()
    group = State()
    confirm = State()


class AddScheduleSG(StatesGroup):
    date = State()  # Дата пары
    group = State()  # Группа пары
    class_ = State()  # Номер пары
    academic_subject = State()  # Учебный предмет
    class_type = State()  # Тип пары (лекция, практика)
    audience = State()  # Аудитория
