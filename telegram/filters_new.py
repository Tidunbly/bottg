from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter
from create_bot import db

class IsAdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:

        user_id = event.from_user.id
        return await db.is_admin_exists(user_id)

class Answer(StatesGroup):
    waiting_for_query = State()
    waiting_for_answer = State()
    waiting_for_place = State()
    waiting_for_office = State()
    waiting_for_id = State()
    waiting_for_support = State()
    waiting_for_rate_1 = State()
    waiting_for_rate_2 = State()
    waiting_for_rate_3 = State()
    waiting_for_continue = State()
    waiting_for_doc = State()
    waiting_for_add_admin = State()
    waiting_for_delete_admin = State()
    waiting_for_file_to_delete = State()
