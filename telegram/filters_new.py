from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Filter
from aiogram.types import Message


class Answer(StatesGroup):
    waiting_for_query = State()
    waiting_for_answer = State()
    waiting_for_place = State()
    waiting_for_office = State()
    waiting_for_id = State()
    waiting_for_support = State()  # Доделать
    waiting_for_rate_1 = State()
    waiting_for_rate_2 = State()
    waiting_for_rate_3 = State()
    waiting_for_continue = State()
