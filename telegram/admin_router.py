from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery
from filters_new import *
from main import *
from kyboards import *
from aiogram import F, Router
from config import *
from create_bot import bot, db

admin_router = Router()


@admin_router.message(Command('cancel'), F.chat.in_(AdminChatId))
async def cancel_command(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer('Вы вышли из состояния.')


@admin_router.callback_query(F.data == 'button_cancel')
async def cancel_button(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer('Вы вышли из состояния.', reply_markup=builder_admin.as_markup())
    await call.answer()


@admin_router.message(Command('menu'), F.chat.func(lambda chat: chat.id == AdminChatId))
async def help_command(msg: Message):
    await msg.answer('Доступные команды:\n'
                     '/cancel - отменить выбор запроса\n/kb - вызвать клавиатуру'
                     '/doc =прикрепленный файл= -добавить файл в базу знаний', reply_markup=builder_menu.as_markup())


@admin_router.callback_query(F.data == 'button_help')
async def help_button(call: CallbackQuery):
    await call.message.answer(
        'Доступные команды:\n'
        '/cancel - отменить выбор запроса\n/kb - вызвать клавиатуру'
        '/doc =прикрепленный файл= -добавить файл в базу знаний', reply_markup=builder_menu.as_markup())
    await call.answer()


@admin_router.message(Command('doc'), F.chat.func(lambda chat: chat.id == AdminChatId))
async def add_document(msg: Message):
    document = msg.document
    doc_id = document.file_id
    doc_name = document.file_name
    file = await bot.get_file(doc_id)
    downloaded_file = await bot.download_file(file.file_path)

    await msg.answer('Файл добавлен в базу знаний!')
    with open(rf"C:\Users\Никита\Documents\AiChatBot2\{doc_name}", "wb") as new_file:
        new_file.write(downloaded_file.read())

    json_maker(mainpath, json_file_path)


@admin_router.message(F.chat.func(lambda chat: chat.id == AdminChatId), Command("answer"))
async def answer_command(msg: Message, state: FSMContext):
    _, _, id = msg.text.partition(" ")
    queries = await db.get_query_by_id(id)
    query = queries
    if queries and query[5] != 'Решается':
        await db.update_query_status(query[0], 'Решается')
        try:
            await msg.answer(f"Запрос от: {query[1]}\n"
                             f"Локация: {query[4]}\n"
                             f"Текст запроса: {query[2]}"
                             f'Ответ ИИ: {query[3]}', reply_markup=builder_cancel.as_markup())

            await state.set_state(Answer.waiting_for_answer)

            await state.update_data(query_id=query[0], user_id=query[1])
        except Exception as e:
            await db.update_query_status(query[0], 'Не решён')

    else:
        await msg.answer("Неверный id или запрос уже решается!")


def shorten_text(text, max_length=100):
    return text[:max_length] + "..." if len(text) > max_length else text


@admin_router.callback_query(F.data.startswith("page_"))
async def paginate(call: CallbackQuery):
    page = int(call.data.split("_")[1])
    queries = await db.get_unanswered_query()
    chunks = [queries[i:i + 5] for i in range(0, len(queries), 5)]
    await send_query_chunk(call.message,call, chunks, page)
    await call.answer()


@admin_router.callback_query(F.data == 'button_all')
async def all_button(call: CallbackQuery):
    queries = await db.get_unanswered_query()

    if queries:
        chunk_size = 5
        chunks = [queries[i:i + chunk_size] for i in range(0, len(queries), chunk_size)]
        await send_query_chunk(call.message, call, chunks, 0)
    else:
        await call.message.answer('Нерешенных запросов нет.')


async def send_query_chunk(msg, call, chunks, page):
    response = f"Список нерешенных запросов (страница {page + 1} из {len(chunks)}):\n\n"
    for query in chunks[page]:
        response += (
            f"ID: {query[0]}\n"
            f"Пользователь: {query[1]}\n"
            f"Запрос: {shorten_text(query[2])}\n"
            f"Ответ: {shorten_text(query[3])}\n"
            f"Локация   : {query[4]}\n"
            f"Статус: {query[5]}\n"
            "------------------------\n"
        )

    builder_page = InlineKeyboardBuilder()
    builder_page.add(
        InlineKeyboardButton(text=f'Ответить{emoji.emojize(":writing_hand:")}', callback_data='button_start_answer'))
    builder_page.add(InlineKeyboardButton(text='Меню🛎️', callback_data='button_help'))

    if page > 0:
        builder_page.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{page - 1}"))
    if page < len(chunks) - 1:
        builder_page.add(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"page_{page + 1}"))

    await msg.edit_text(response, reply_markup=builder_page.as_markup())
    await call.answer()



@admin_router.callback_query(F.data == 'button_start_answer')
async def start_answer_handler(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Отправьте id запроса.')
    await state.set_state(Answer.waiting_for_id)
    await call.answer()


@admin_router.message(Answer.waiting_for_id)
async def waiting_for_id_handler(msg: Message, state: FSMContext):
    id = msg.text
    queries = await db.get_query_by_id(id)
    query = queries
    if queries and query[5] != 'Решается':
        try:
            await msg.answer(f"Запрос от: {query[1]}\n"
                             f"Локация: {query[4]}\n"
                             f"Текст запроса: {query[2]}\n"
                             f"Текст ответа: {query[3]}", reply_markup=builder_answer.as_markup())

            await state.update_data(query_id=query[0], user_id=query[1])
        except Exception as e:
            await msg.answer('ошибка')
    else:
        await msg.answer("Неверный id или запрос уже решается!")


@admin_router.callback_query(F.data == 'button_answer')
async def answer_button(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Введите сообщение для отправки.')

    data = await state.get_data()
    query_id = data.get('query_id')
    user_id = data.get('user_id')
    admin_id = call.from_user.id

    await state.set_state(Answer.waiting_for_answer)
    await db.update_query_status(query_id, 'Решается', admin_id)

    await bot.send_message(user_id, 'Ваш запрос принят сотрудником.')
    await call.answer()


@admin_router.message(Answer.waiting_for_answer)
async def answer_process(msg: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get('user_id')

    text = msg.text
    await state.update_data(admin_text=text)
    await msg.answer("Ответ был отправлен", reply_markup=builder_answering.as_markup())
    await bot.send_message(chat_id=user_id, text=f"Сотрудник: \n{text}")


@admin_router.callback_query(F.data == 'button_close')
async def close_query(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    query_id = data.get('query_id')
    text = data.get('admin_text', '')

    await db.update_query_id(query_id, text, 'Решён')
    await call.message.answer('Запрос закрыт.', reply_markup=builder_admin.as_markup())
    user_id = data.get('user_id')

    await bot.send_message(user_id, 'Сотрудник закрыл ваш запрос.', reply_markup=builder_user.as_markup())

    await call.answer()
    await state.clear()


@admin_router.message(Command('delete'), F.chat.func(lambda chat: chat.id == AdminChatId))
async def delete_command(msg: Message):
    queries = await db.get_all_query()
    if not queries:
        await msg.answer('Запросов нет')
        return

    try:
        query_id = int(msg.text.split()[1])
    except (IndexError, ValueError):
        await msg.answer('Ошибка ввода id')
    try:
        if not any(query[0] == query_id for query in queries):
            await msg.reply('Запроса с таким id нет')
            return
    except:
        await msg.answer('Ошибка ввода id')

    await db.delete_query(query_id)

    await msg.reply(f'Запрос с id = {query_id} удален')


@admin_router.callback_query(F.data == 'button_rates')
async def rates_button(call: CallbackQuery):
    rates = await db.get_all_rates()


    page_size = 5
    chunks = [rates[i:i + page_size] for i in range(0, len(rates), page_size)]

    page = 0

    response = f"Список оценок (страница {page + 1} из {len(chunks)}):\n\n"
    for rate in chunks[page]:
        response += (
            f"ID: {rate[0]}\n"
            f"ID запроса: {rate[1]}\n"
            f"Запрос: {shorten_text(rate[2])}\n"
            f"Оценка: {rate[3]}\n"
            "------------------------\n"
        )

    builder_page_rate = InlineKeyboardBuilder()
    builder_page_rate.add(InlineKeyboardButton(text='Меню🛎️', callback_data='button_help'))

    if page > 0:
        builder_page_rate.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"rate_page_{page - 1}"))
    if page < len(chunks) - 1:
        builder_page_rate.add(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"rate_page_{page + 1}"))

    await call.message.answer(response, reply_markup=builder_page_rate.as_markup())
    await call.answer()


@admin_router.callback_query(F.data.startswith("rate_page_"))
async def handle_rate_pagination(call: CallbackQuery):
    page = int(call.data.split("_")[-1])
    rates = await db.get_all_rates()

    page_size = 5
    chunks = [rates[i:i + page_size] for i in range(0, len(rates), page_size)]

    response = f"Список оценок (страница {page + 1} из {len(chunks)}):\n\n"
    for rate in chunks[page]:
        response += (
            f"ID: {rate[0]}\n"
            f"ID запроса: {rate[1]}\n"
            f"Запрос: {shorten_text(rate[2])}\n"
            f"Оценка: {rate[3]}\n"
            "------------------------\n"
        )

    builder_page_rate = InlineKeyboardBuilder()
    if page > 0:
        builder_page_rate.add(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"rate_page_{page - 1}"))
    if page < len(chunks) - 1:
        builder_page_rate.add(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"rate_page_{page + 1}"))

    await call.message.edit_text(response, reply_markup=builder_page_rate.as_markup())


@admin_router.callback_query(F.data == 'button_history')
async def history_button(call: CallbackQuery):
    queries = await db.get_all_query()

    if queries:
        chunk_size = 5
        chunks = [queries[i:i + chunk_size] for i in range(0, len(queries), chunk_size)]
        await send_query_chunk(call.message, chunks, 0)
    else:
        await call.message.answer('Нерешенных запросов нет.')
    await call.answer()


@admin_router.message(Command('kb'), F.chat.func(lambda chat: chat.id == AdminChatId))
async def keyboard_command(msg: Message):
    await msg.answer('Клавиатура вызвана', reply_markup=keyboard)
