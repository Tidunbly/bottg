from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
import emoji

builder = InlineKeyboardBuilder()
builder.add(InlineKeyboardButton(text=f"Запрос решён{emoji.emojize(':OK_hand:')}", callback_data="button_solved"))
builder.add(
    InlineKeyboardButton(text=f"Вызвать сотрудника{emoji.emojize(':technologist:')}", callback_data="button_unsolved"))

kb_list = [[KeyboardButton(text='/help'), KeyboardButton(text='/cancel')]]
keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=False)

# Кнопки админ панели
builder_admin = InlineKeyboardBuilder()
builder_admin.row(InlineKeyboardButton(text='Список запросов📃', callback_data='button_all'))
builder_admin.row(InlineKeyboardButton(text='Меню🛎️', callback_data='button_help'))
builder_admin.add(InlineKeyboardButton(text='Отмена❌', callback_data='button_cancel'))
builder_admin.add(InlineKeyboardButton(text=f'Оценки{emoji.emojize(":thumbs_up:")}', callback_data='button_rates'))

builder_cancel = InlineKeyboardBuilder()
builder_cancel.add(InlineKeyboardButton(text='Отмена❌', callback_data='button_cancel'))

builder_menu = InlineKeyboardBuilder()
builder_menu.row(InlineKeyboardButton(text='Список запросов📃', callback_data='button_all'))
builder_menu.row(InlineKeyboardButton(text='Отмена❌', callback_data='button_cancel'))
builder_menu.add(InlineKeyboardButton(text=f'Оценки{emoji.emojize(":thumbs_up:")}', callback_data='button_rates'))

builder_answer = InlineKeyboardBuilder()
builder_answer.add(
    InlineKeyboardButton(text=f'Ответить{emoji.emojize(":writing_hand:")}', callback_data='button_answer'))
builder_answer.add(InlineKeyboardButton(text='Отмена❌', callback_data='button_cancel'))
builder_answer.add(InlineKeyboardButton(text='Завершить✅', callback_data='button_close'))

builder_answering = InlineKeyboardBuilder()
builder_answering.add(InlineKeyboardButton(text='Завершить✅', callback_data='button_close'))

builder_user = InlineKeyboardBuilder()
builder_user.add(
    InlineKeyboardButton(text=f'Отправить новый запрос{emoji.emojize(":speech_balloon:")}', callback_data='new_query'))

builder_rate = InlineKeyboardBuilder()
builder_rate.add(InlineKeyboardButton(text=f'{emoji.emojize(":keycap_1:")}', callback_data='rate_1'))
builder_rate.add(InlineKeyboardButton(text=f'{emoji.emojize(":keycap_2:")}', callback_data='rate_2'))
builder_rate.add(InlineKeyboardButton(text=f'{emoji.emojize(":keycap_3:")}', callback_data='rate_3'))
builder_rate.add(InlineKeyboardButton(text=f'{emoji.emojize(":keycap_4:")}', callback_data='rate_4'))
builder_rate.add(InlineKeyboardButton(text=f'{emoji.emojize(":keycap_5:")}', callback_data='rate_5'))
