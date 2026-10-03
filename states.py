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


class GameState(StatesGroup):
    waiting_opponent = State()
    answering = State()