from aiogram.fsm.state import State, StatesGroup


class UnregisteredSG(StatesGroup):
    group_token = State()
    student_name = State()
