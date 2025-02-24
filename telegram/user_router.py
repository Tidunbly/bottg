from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, FSInputFile
from filters_new import *
from main import *
from kyboards import *
from aiogram import F, Router
from config import *
from create_bot import bot, db

user_router = Router()


@user_router.message(F.chat.func(lambda chat: chat.id != AdminChatId), CommandStart())
async def command_start_handler(msg: Message, state: FSMContext):
    await msg.answer(f"Здравствуйте {msg.from_user.full_name}!")

    photo = FSInputFile(r"C:\Users\Никита\Documents\I-OiP04hzkg.jpg")
    await bot.send_photo(msg.from_user.id, photo, caption='Отправьте номер корпуса. Например: 8б')
    await state.set_state(Answer.waiting_for_place)


@user_router.message(F.chat.func(lambda chat: chat.id != AdminChatId), Answer.waiting_for_place)
async def place_handler(msg: Message, state: FSMContext):
    building = msg.text

    await state.update_data(building=building)
    await msg.answer('Введите номер кабинета или уточните локацию текстом. Например: 234 или У главного входа слева')
    await state.set_state(Answer.waiting_for_office)


@user_router.message(F.chat.func(lambda chat: chat.id != AdminChatId), Answer.waiting_for_office)
async def office_handler(msg: Message, state: FSMContext):
    office = msg.text
    await state.update_data(office=office)
    await state.set_state(Answer.waiting_for_query)
    await msg.answer('Отправьте интересующий вас вопрос и мы постараемся на него ответить.')


@user_router.message(F.chat.func(lambda chat: chat.id != AdminChatId), Answer.waiting_for_query)
async def req_handler(msg: Message, state: FSMContext):
    await msg.answer("Спасибо за ваш запрос❤ Пожалуйста дождитесь ответа от нашего интеллектуального ассистента!🦾")
    data = await state.get_data()

    from_user_msg = msg.text
    building = data.get('building')
    office = data.get('office')


    query_id = await db.add_query(msg.from_user.id, from_user_msg, f'{building} {office}', '', 'Не решён')

    await state.update_data(query_id=query_id)


    response = await rag_answer_with_history(question=from_user_msg, query_id=query_id)



    await db.update_query_response(query_id=query_id, answer=response)

    await state.update_data(from_user_msg=from_user_msg, response=response)
    await state.set_state(Answer.waiting_for_continue)

    await msg.answer(response, parse_mode="Markdown")
    await msg.answer("Нам удалось вам помочь?", reply_markup=builder.as_markup())


@user_router.message(Answer.waiting_for_continue)
async def cont_handler(msg: Message, state: FSMContext):
    data = await state.get_data()
    query_id = data.get('query_id')
    from_user_msg = msg.text

    response = await rag_answer_with_history(question=from_user_msg, query_id=query_id)

    await msg.answer(response, parse_mode="Markdown", reply_markup=builder.as_markup())



@user_router.callback_query(F.data == "button_solved")
async def solved_button(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    from_user_msg = data.get("from_user_msg", "")
    # class_of_question = data.get("class_of_question", "")

    query_id = data.get('query_id')

    await callback.message.answer("Были рады помочь!❤ Оцените достоверность ответа", reply_markup=builder_rate.as_markup())

    await db.update_query_status(query_id=query_id, status='Решён', admin_id=None)

    await db.add_query_to_rating(query_id, from_user_msg)
    await delete_session_history(query_id)

    # data_to_log = f"{datetime.datetime.now()} \nЗапрос: {from_user_msg} \nТип: {class_of_question} \nСтатус: Решён\n"
    # with open(logs_path, "a", encoding="utf-8") as file:
    #     file.write(data_to_log + "\n")

    await state.set_state(Answer.waiting_for_rate_1)
    await callback.answer()


@user_router.callback_query(F.data == "button_unsolved")
async def unsolved_button(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    from_user_msg = data.get("from_user_msg", "")
    # class_of_question = data.get("class_of_question", "")
    query_id = data.get('query_id')

    await callback.message.answer("Ваш запрос передан сотруднику технической поддержки.")

    # data_to_log = f"{datetime.datetime.now()} \nЗапрос: {from_user_msg} \nТип: {class_of_question} \nСтатус: Не решён\n"
    # with open(logs_path, "a", encoding="utf-8") as file:
    #     file.write(data_to_log + "\n")

    await db.update_query_status(query_id=query_id, status='Не решён', admin_id=None)
    await delete_session_history(query_id)



    await bot.send_message(AdminChatId,
                           f"Новый запрос от {callback.from_user.full_name} - @{callback.from_user.username} - {callback.from_user.id}:\n {from_user_msg}")

    await state.set_state(Answer.waiting_for_support)
    await callback.answer()


@user_router.callback_query(F.data == 'new_query')
async def new_query_button(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введите номер корпуса.")
    await state.set_state(Answer.waiting_for_place)
    await call.answer()


@user_router.callback_query(Answer.waiting_for_rate_1, F.data.startswith('rate_'))
async def rate_buttons(call: CallbackQuery, state: FSMContext):

    rate_1 = call.data[-1]

    await state.update_data(rate_1=rate_1)

    await call.message.answer('Оцените полноту ответа', reply_markup=builder_rate.as_markup())
    await state.set_state(Answer.waiting_for_rate_2)
    await call.answer()


@user_router.callback_query(Answer.waiting_for_rate_2, F.data.startswith('rate_'))
async def rate_buttons(call: CallbackQuery, state: FSMContext):

    rate_2 = call.data[-1]
    await call.message.answer('Оцените достоверность ответа', reply_markup=builder_rate.as_markup())
    await state.update_data(rate_2=rate_2)

    await state.set_state(Answer.waiting_for_rate_3)
    await call.answer()


@user_router.callback_query(Answer.waiting_for_rate_3, F.data.startswith('rate_'))
async def rate_buttons(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    query_id = data.get('query_id')
    rate_1 = data.get('rate_1')
    rate_2 = data.get('rate_2')
    rate_3 = call.data[-1]

    await state.update_data(rate_=rate_3)

    await db.add_rate_to_query(f'Достоверность: {rate_1}, Полнота: {rate_2}, Удобство: {rate_3}', query_id)
    await call.message.answer('Спасибо за вашу оценку!', reply_markup=builder_user.as_markup())

    await state.clear()
    await call.answer()


@user_router.message(Answer.waiting_for_support)
async def support_handler(msg: Message, state: FSMContext):
    data = await state.get_data()
    query_id = data.get('query_id')

    query = await db.get_query_by_id(query_id)
    if query[5] == 'Решается':
        admin_id = query[6]
        await bot.send_message(admin_id, f'Пользователь: {msg.text}')
        # await bot.copy_message()
