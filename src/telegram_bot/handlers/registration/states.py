from aiogram.fsm.state import State, StatesGroup


class RegistrationSG(StatesGroup):
    group_token = State()
    student_name = State()
