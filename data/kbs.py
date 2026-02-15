from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from data.strings import current_processes_text, add_process_text


back_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отмена')]],
      resize_keyboard=True)

start_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text=current_processes_text), KeyboardButton(text=add_process_text)]], 
    resize_keyboard=True)