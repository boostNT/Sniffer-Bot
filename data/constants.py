from pyrogram import Client
from pyrogram.types import Gift, User
from aiogram import Bot, Dispatcher
from aiogram.fsm.state import StatesGroup, State
from cryptography.fernet import Fernet
from typing import List
from pytz import timezone


class Form(StatesGroup):
    wait_username = State()


class SniffingUser:
    profile: User
    gifts: List[Gift]


TOKEN = '' # замените на токен своего бота с @BotFather
ADMINS = {} # вайт лист


ENCRYPT_KEY = b'rRu-U-nqZUsPi9jcZ2bvdkxgtu8v-jFX78jJnh2i-ek=' # можете поменять с помощью f.generate_key() (это ключ для шифрования и дешифрования объекта данных о пользователе, которые будут храниться в бд)
DB_NAME = './main.db'


api_id = 123123123 
api_hash = '123123123'
client = Client('main', api_id=api_id, api_hash=api_hash) # замените на свои данные (https://my.telegram.org/auth)

bot = Bot(TOKEN)
f = Fernet(ENCRYPT_KEY)
dp = Dispatcher(bot=bot)
tz = timezone('Europe/Moscow')