from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery
from filters_new import *
from main import *
from kyboards import *
from aiogram import F, Router
from config import *
from create_bot import bot, db
from vectore_store_manager import create_vectorstore
import main
from jsonmaker import *
admin_router = Router()



@admin_router.message(CommandStart(), IsAdminFilter())
async def start_admin(msg: Message):
    builder_start = InlineKeyboardBuilder()
    builder_start.row(InlineKeyboardButton(text='Меню🛎️', callback_data='button_menu'))

    await msg.answer(
        'Здравствуйте! Вы вошли как сотрудник, весь функционал доступен по кнопке ниже или по команде /menu.\n'
        'Настройки доступны по команде /settings.',
        reply_markup=builder_start.as_markup())


@admin_router.callback_query(F.data == 'button_cancel', IsAdminFilter())
async def cancel_button(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text('Вы вышли из состояния.', reply_markup=builder_admin.as_markup())
    await call.answer()


@admin_router.message(Command('menu'), IsAdminFilter())
async def help_command(msg: Message):
    await msg.answer('Бот для удобного ответа на пользовательские запросы.\n\n'
                     '', reply_markup=builder_menu.as_markup())


@admin_router.callback_query(F.data == 'button_menu', IsAdminFilter())
async def help_button(call: CallbackQuery):
    await call.message.edit_text(
        'Бот для удобного ответа на пользовательские запросы.\n\n'
        '', reply_markup=builder_menu.as_markup())
    await call.answer()


@admin_router.callback_query(F.data == 'button_add_doc', IsAdminFilter())
async def add_file_button(call: CallbackQuery, state: FSMContext):
    builder_add_file = InlineKeyboardBuilder()
    builder_add_file.add(InlineKeyboardButton(text='< Назад', callback_data='button_show_files'))

    await call.message.edit_text('Отправьте файл в формате txt.', reply_markup=builder_add_file.as_markup())
    await state.set_state(Answer.waiting_for_doc)


@admin_router.message(Answer.waiting_for_doc, F.document, IsAdminFilter())
async def add_file_handler(msg: Message):
    builder_add_file = InlineKeyboardBuilder()
    builder_add_file.add(InlineKeyboardButton(text='< Назад', callback_data='button_show_files'))

    if msg.document:
        document = msg.document
        doc_id = document.file_id
        doc_name = document.file_name
        file = await bot.get_file(doc_id)
        downloaded_file = await bot.download_file(file.file_path)

        await msg.answer('Файл добавлен в базу знаний!', reply_markup=builder_add_file.as_markup())
        with open(rf"AiChatBot2\{doc_name}", "wb") as new_file:
            new_file.write(downloaded_file.read())

        json_maker(mainpath, json_file_path)
    else:
        await msg.answer('Произошла ошибка! Проверьте файл на целостность и попробуйте еще раз',
                         reply_markup=builder_cancel.as_markup())


def shorten_text(text, max_length=100):
    return text[:max_length] + "..." if len(text) > max_length else text


@admin_router.callback_query(F.data.startswith("page_"), IsAdminFilter())
async def paginate(call: CallbackQuery):
    page = int(call.data.split("_")[1])
    queries = await db.get_unanswered_query()
    chunks = [queries[i:i + 5] for i in range(0, len(queries), 5)]
    await send_query_chunk(call.message, call, chunks, page)
    await call.answer()


@admin_router.callback_query(F.data == 'button_all', IsAdminFilter())
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

    builder_page_opened = InlineKeyboardBuilder()
    builder_page_opened.add(
        InlineKeyboardButton(text=f'Выбрать запрос{emoji.emojize(":writing_hand:")}',
                             callback_data='button_start_answer'))

    if page > 0 or page < len(chunks) - 1:
        row_buttons = []  # Создаем список для кнопок

        if page > 0:
            row_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))

        if page < len(chunks) - 1:
            row_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))

        # Добавляем кнопки в один ряд
        builder_page_opened.row(*row_buttons)

    builder_page_opened.row(InlineKeyboardButton(text='Решённые🎉', callback_data='button_closed'))
    builder_page_opened.row(InlineKeyboardButton(text='< Назад', callback_data='button_menu'))

    await msg.edit_text(response, reply_markup=builder_page_opened.as_markup())
    await call.answer()


@admin_router.callback_query(F.data.startswith("page_second_"), IsAdminFilter())
async def paginate(call: CallbackQuery):
    page = int(call.data.split("_")[1])
    queries = await db.get_unanswered_query()
    chunks = [queries[i:i + 5] for i in range(0, len(queries), 5)]
    await send_query_chunk(call.message, call, chunks, page)
    await call.answer()


@admin_router.callback_query(F.data == 'button_closed', IsAdminFilter())
async def closed_button(call: CallbackQuery):
    queries = await db.get_answered_query()

    if queries:
        chunk_size = 5
        chunks = [queries[i:i + chunk_size] for i in range(0, len(queries), chunk_size)]
        await send_query_closed_chunk(call.message, call, chunks, 0)
    else:
        await call.message.answer('Решённых запросов нет.')


async def send_query_closed_chunk(msg, call, chunks, page):
    response = f"Список решённых запросов (страница {page + 1} из {len(chunks)}):\n\n"
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

    builder_page_closed = InlineKeyboardBuilder()

    if page > 0 or page < len(chunks) - 1:
        row_buttons = []

        if page > 0:
            row_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))

        if page < len(chunks) - 1:
            row_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))

        builder_page_closed.row(*row_buttons)

    builder_page_closed.row(InlineKeyboardButton(text='Не решённые⏳', callback_data='button_all'))
    builder_page_closed.row(InlineKeyboardButton(text='< Назад', callback_data='button_menu'))

    await msg.edit_text(response, reply_markup=builder_page_closed.as_markup())
    await call.answer()


@admin_router.callback_query(F.data == 'button_start_answer', IsAdminFilter())
async def start_answer_handler(call: CallbackQuery, state: FSMContext):
    builder_start_answer = InlineKeyboardBuilder()
    builder_start_answer.add(InlineKeyboardButton(text='< Назад', callback_data='button_all'))
    await call.message.edit_text('Отправьте id запроса.', reply_markup=builder_start_answer.as_markup())
    await state.set_state(Answer.waiting_for_id)
    await call.answer()


@admin_router.message(Answer.waiting_for_id, IsAdminFilter())
async def waiting_for_id_handler(msg: Message, state: FSMContext):
    id = msg.text
    queries = await db.get_query_by_id(id)
    query = queries

    if queries and query[5] != 'Решается':
        builder_waiting_for_id = InlineKeyboardBuilder()
        builder_waiting_for_id.add(
            InlineKeyboardButton(text=f'Ответить{emoji.emojize(":writing_hand:")}', callback_data='button_answer'))
        builder_waiting_for_id.add(InlineKeyboardButton(text='Завершить✅', callback_data='button_close'))
        builder_waiting_for_id.row(InlineKeyboardButton(text='< Назад', callback_data='button_all'))

        try:
            await msg.answer(f"Запрос от: {query[1]}\n"
                             f"Локация: {query[4]}\n"
                             f"Текст запроса: {query[2]}\n"
                             f"Текст ответа: {query[3]}", reply_markup=builder_waiting_for_id.as_markup())

            await state.update_data(query_id=query[0], user_id=query[1])
        except Exception as e:
            await msg.answer('ошибка')
    else:
        await msg.answer("Неверный id или запрос уже решается!")


@admin_router.callback_query(F.data == 'button_answer', IsAdminFilter())
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


@admin_router.message(Answer.waiting_for_answer, IsAdminFilter())
async def answer_process(msg: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get('user_id')

    if not user_id:
        await msg.answer("Ошибка: не найден ID пользователя.")
        return

    if msg.text:  # Если это текст
        text = msg.text
        await state.update_data(admin_text=text)

    await msg.answer("Ответ был отправлен", reply_markup=builder_answering.as_markup())
    await bot.send_message(chat_id=user_id, text='Сотрудник: ')
    await bot.copy_message(chat_id=user_id, from_chat_id=msg.chat.id, message_id=msg.message_id)


@admin_router.callback_query(F.data == 'button_close', IsAdminFilter())
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


# @admin_router.message(Command('delete'), IsAdminFilter())
# async def delete_command(msg: Message):
#     queries = await db.get_all_query()
#     if not queries:
#         await msg.answer('Запросов нет')
#         return
#
#     try:
#         query_id = int(msg.text.split()[1])
#     except (IndexError, ValueError):
#         await msg.answer('Ошибка ввода id')
#     try:
#         if not any(query[0] == query_id for query in queries):
#             await msg.reply('Запроса с таким id нет')
#             return
#     except:
#         await msg.answer('Ошибка ввода id')
#
#     await db.delete_query(query_id)
#
#     await msg.reply(f'Запрос с id = {query_id} удален')


@admin_router.callback_query(F.data == 'button_rates', IsAdminFilter())
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

    if page > 0 or page < len(chunks) - 1:
        row_buttons = []

        if page > 0:
            row_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"rate_page_{page - 1}"))

        if page < len(chunks) - 1:
            row_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"rate_page_{page + 1}"))

        builder_page_rate.row(*row_buttons)

    builder_page_rate.row(InlineKeyboardButton(text='< Назад', callback_data='button_menu'))

    await call.message.edit_text(response, reply_markup=builder_page_rate.as_markup())
    await call.answer()


@admin_router.callback_query(F.data.startswith("rate_page_"), IsAdminFilter())
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

    if page > 0 or page < len(chunks) - 1:
        row_buttons = []

        if page > 0:
            row_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"rate_page_{page - 1}"))

        if page < len(chunks) - 1:
            row_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"rate_page_{page + 1}"))

        builder_page_rate.row(*row_buttons)

    builder_page_rate.row(InlineKeyboardButton(text='< Назад', callback_data='button_menu'))

    await call.message.edit_text(response, reply_markup=builder_page_rate.as_markup())


async def get_settings_keyboard(admin_id):
    status = await db.get_admin_status(admin_id)
    builder_setting = InlineKeyboardBuilder()

    # Кнопка для изменения статуса
    builder_setting.add(InlineKeyboardButton(
        text=f'Изменить статус 🔄',
        callback_data=f'toggle_status_{admin_id}'
    ))

    # Остальные кнопки
    builder_setting.row(InlineKeyboardButton(text='Добавить сотрудника➕', callback_data='button_add_admin'))
    builder_setting.add(InlineKeyboardButton(text='Удалить сотрудника🗑️', callback_data='button_delete_admin'))
    builder_setting.row(InlineKeyboardButton(text='Показать файлы 📂', callback_data='button_show_files'))
    builder_setting.row(InlineKeyboardButton(text='< Назад', callback_data='button_menu'))

    return builder_setting.as_markup()


@admin_router.message(Command("settings"),IsAdminFilter())
async def settings_command(msg: Message):
    admin_id = msg.from_user.id
    status = await db.get_admin_status(admin_id)

    # Форматируем текст состояния
    status_text = "активен ✅" if status == "active" else "неактивен ❌"

    # Отправляем сообщение с клавиатурой настроек
    await msg.answer(
        f'👤{admin_id}\n\nСостояние: {status_text}',
        reply_markup=await get_settings_keyboard(admin_id)
    )


@admin_router.callback_query(F.data == 'button_settings', IsAdminFilter())
async def setting_button(call: CallbackQuery):
    admin_id = call.from_user.id
    status = await db.get_admin_status(admin_id)

    status_text = "активен ✅" if status == "active" else "неактивен ❌"
    await call.message.edit_text(
        f'👤{admin_id}\n\nСостояние: {status_text}',
        reply_markup=await get_settings_keyboard(admin_id)
    )
    await call.answer()


@admin_router.callback_query(F.data.startswith('toggle_status_'), IsAdminFilter())
async def toggle_status_handler(call: CallbackQuery):
    admin_id = int(call.data.split('_')[-1])  # Получаем ID администратора
    current_status = await db.get_admin_status(admin_id)  # Получаем текущий статус

    # Меняем статус на противоположный
    new_status = "inactive" if current_status == "active" else "active"
    await db.update_admin_status(admin_id, new_status)  # Обновляем статус в базе данных

    # Форматируем текст состояния с эмодзи
    status_text = "активен ✅" if new_status == "active" else "неактивен ❌"

    # Обновляем сообщение с новым статусом и клавиатурой
    await call.message.edit_text(
        f'👤{admin_id}\n\nСостояние: {status_text}',  # Текст состояния в одной строке
        reply_markup=await get_settings_keyboard(admin_id)
    )
    await call.answer(f'Статус изменен на {status_text}')


@admin_router.callback_query(F.data == 'button_add_admin', IsAdminFilter())
async def add_admin_button(call: CallbackQuery, state: FSMContext):
    builder_add_admin = InlineKeyboardBuilder()
    builder_add_admin.add(InlineKeyboardButton(text='< Назад', callback_data='button_settings'))

    await call.message.edit_text('Перешлите сообщение от пользователя, которого хотите добавить в сотрудники.',
                                 reply_markup=builder_add_admin.as_markup())
    await state.set_state(Answer.waiting_for_add_admin)
    await call.answer()


@admin_router.message(Answer.waiting_for_add_admin, IsAdminFilter())
async def add_admin_handler(msg: Message):
    try:

        user_id = msg.forward_from.id
        is_exists = await db.is_admin_exists(user_id)
        if not is_exists:
            await db.add_admin(user_id)
            await msg.answer('Сотрудник успешно добавлен!', reply_markup=builder_menu.as_markup())

        else:
            await msg.answer('Сотрудник уже добавлен! Вы можете попробовать еще раз или отменить операцию.',
                             reply_markup=builder_cancel.as_markup())

    except Exception as e:
        await msg.answer('Произошла ошибка! Попробуйте еще раз!', reply_markup=builder_menu.as_markup())


@admin_router.callback_query(F.data == 'button_delete_admin', IsAdminFilter())
async def delete_admin_button(call: CallbackQuery, state: FSMContext):
    builder_delete_admin = InlineKeyboardBuilder()
    builder_delete_admin.add(InlineKeyboardButton(text='< Назад', callback_data='button_settings'))

    await call.message.edit_text('Перешлите сообщение от пользователя, которого хотите удалить из сотрудников.',
                                 reply_markup=builder_delete_admin.as_markup())
    await state.set_state(Answer.waiting_for_delete_admin)
    await call.answer()


@admin_router.message(Answer.waiting_for_delete_admin, IsAdminFilter())
async def add_admin_handler(msg: Message):
    try:
        user_id = msg.forward_from.id
        is_exists = await db.is_admin_exists(user_id)
        if is_exists:
            await db.delete_admin(user_id)
            await msg.answer('Сотрудник успешно удален!', reply_markup=builder_menu.as_markup())

        else:
            await msg.answer('Сотрудника нет в системе! Вы можете попробовать еще раз или отменить операцию.',
                             reply_markup=builder_cancel.as_markup())

    except Exception as e:
        await msg.answer('Произошла ошибка! Попробуйте еще раз!', reply_markup=builder_menu.as_markup())


@admin_router.callback_query(F.data == 'button_show_files', IsAdminFilter())
async def show_files_button(call: CallbackQuery):
    await paginate_files(call, page=0)


@admin_router.callback_query(F.data.startswith('files_page_'), IsAdminFilter())
async def paginate_files(call: CallbackQuery, page: int = None):
    if page is None:
        try:
            page = int(call.data.split('_')[-1])  # Получаем номер страницы из callback_data
        except (IndexError, ValueError):
            await call.message.answer("Ошибка: неверный формат callback_data.")
            return

    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            documents = json.load(f)

        if not documents:
            await call.message.answer("Файлов в базе знаний пока нет.")
            return

        page_size = 5
        chunks = [documents[i:i + page_size] for i in range(0, len(documents), page_size)]

        if page >= len(chunks) or page < 0:
            await call.message.answer("Страница не найдена.")
            return

        start_index = page * page_size

        file_list = "\n".join(
            [f"{start_index + i + 1}. {doc['title']}" for i, doc in enumerate(chunks[page])]
        )

        builder_files = InlineKeyboardBuilder()

        builder_files.row(
            InlineKeyboardButton(text='Удалить инструкцию🗑️', callback_data='button_delete_doc'),
            InlineKeyboardButton(text='Добавить инструкцию💡', callback_data='button_add_doc')
        )

        if page > 0 or page < len(chunks) - 1:
            row_buttons_files = []

            if page > 0:
                row_buttons_files.append(InlineKeyboardButton(text="⬅️", callback_data=f"files_page_{page - 1}"))

            if page < len(chunks) - 1:
                row_buttons_files.append(InlineKeyboardButton(text="➡️", callback_data=f"files_page_{page + 1}"))

            builder_files.row(*row_buttons_files)

        builder_files.row(InlineKeyboardButton(text=f'< Назад', callback_data='button_settings'))

        # Выводим сообщение с клавиатурой
        await call.message.edit_text(
            f"Список файлов (страница {page + 1} из {len(chunks)}):\n\n{file_list}",
            reply_markup=builder_files.as_markup()
        )
    except Exception as e:
        await call.message.answer(f"Произошла ошибка при чтении файлов: {e}")


@admin_router.callback_query(F.data == 'button_delete_doc', IsAdminFilter())
async def delete_file_button(call: CallbackQuery, state: FSMContext):
    builder_delete_file = InlineKeyboardBuilder()
    builder_delete_file.add(InlineKeyboardButton(text='< Назад', callback_data='button_show_files'))

    await call.message.edit_text("Введите название файла для удаления:", reply_markup=builder_delete_file.as_markup())
    await state.set_state(Answer.waiting_for_file_to_delete)


@admin_router.message(Answer.waiting_for_file_to_delete, F.text, IsAdminFilter())
async def delete_file_handler(msg: Message, state: FSMContext):
    file_name = msg.text.strip()
    builder_delete_file = InlineKeyboardBuilder()
    builder_delete_file.add(InlineKeyboardButton(text='< Назад', callback_data='button_show_files'))

    try:
        # Удаляем TXT-файл
        file_path = os.path.join(mainpath, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            await msg.answer(f"Файл '{file_name}' не найден в директории.",
                             reply_markup=builder_delete_file.as_markup())
            return

        # Удаляем запись из JSON-файла
        if os.path.exists(json_file_path):
            with open(json_file_path, "r", encoding="utf-8") as f:
                documents = json.load(f)

            # Фильтруем документы, удаляя запись с указанным названием
            initial_length = len(documents)
            documents = [doc for doc in documents if doc["title"] != file_name]

            if len(documents) < initial_length:
                with open(json_file_path, "w", encoding="utf-8") as f:
                    json.dump(documents, f, ensure_ascii=False, indent=4)
            else:
                await msg.answer(f"Файл '{file_name}' не найден в JSON.", reply_markup=builder_delete_file.as_markup())
                return

        else:
            await msg.answer("JSON-файл не найден.", reply_markup=builder_delete_file.as_markup())
            return

        # Пересоздаем векторное хранилище

        main.vectorstore = create_vectorstore(json_file_path)  # Используем функцию из vectorstore_manager

        await msg.answer(f"Файл '{file_name}' успешно удален из базы знаний.",
                         reply_markup=builder_delete_file.as_markup())
        await state.clear()

    except Exception as e:
        await msg.answer(f"Произошла ошибка при удалении файла: {e}", reply_markup=builder_delete_file.as_markup())

# @admin_router.message(Command('kb'), F.chat.func(lambda chat: chat.id == AdminChatId))
# async def keyboard_command(msg: Message):
#     await msg.answer('Клавиатура вызвана', reply_markup=keyboard)
