from aiogram import Dispatcher
from aiogram import Bot
from database import DataBase
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import *

TOKEN = tg_token
dp = Dispatcher()
db = DataBase()
storage = MemoryStorage()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))