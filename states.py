from aiogram.fsm.state import State, StatesGroup


class ProfileState(StatesGroup):
    name = State()
    age = State()
    city = State()
    interests = State()
    description = State()
    photo = State()


class QuestionState(StatesGroup):
    answering = State()
    replying = State()
