import asyncio
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors.exceptions import UsernameNotOccupied, UsernameInvalid, PhoneNotOccupied
from models import *
from utils import *
from data import *


@dp.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user
    await database.reg_user(user)
    if user.id not in ADMINS:
        return
    await message.answer('<b>Привет</b>\nЭто бот для отслеживания изменений в аккаунтах других пользователей.', reply_markup=start_kb, parse_mode='HTML')


@dp.message(~StateFilter(*Form.__states__))
async def msg_handler(message: Message, state: FSMContext):
    text = message.text
    uid = message.from_user.id

    if text == back_text:
        await message.answer('<b>Привет</b>\nЭто бот для отслеживания изменений в аккаунтах других пользователей.', reply_markup=start_kb, parse_mode='HTML')

    if text == add_process_text:
        await message.answer('Введи тег аккаунта, который хочешь начать отслеживать:', reply_markup=back_kb)
        await state.set_state(Form.wait_username)

    if text == current_processes_text:
        sniffs_text, sniffs_markup, total = await sniffer.get_sniffs_data(uid)
        if not sniffs_text:
            await message.answer('Процессов нет.')
            return

        await message.answer(f'<b>Твои процессы ({total}):</b>\n\n\n{sniffs_text}\n<b>Выбери какой процесс хочешь удалить:</b>', reply_markup=sniffs_markup, parse_mode='HTML')

    if text == 'Отмена':
        await message.answer('<b>Привет</b>\nЭто бот для отслеживания изменений в аккаунтах других пользователей.', reply_markup=start_kb, parse_mode='HTML')



@dp.callback_query()
async def cb_handler(call: CallbackQuery):
    d = call.data
    uid = call.from_user.id

    if d.startswith('page_'):
        try:
            page = int(d.split('_')[1])
        except:
            return

        sniffs_text, sniffs_markup, total = await sniffer.get_sniffs_data(uid, page=page)
        if not sniffs_text:
            await call.message.edit_text('Процессов нет.')
            return

        await call.message.edit_text(f'<b>Твои процессы ({total}):</b>\n\n\n{sniffs_text}\n<b>Выбери процесс ниже:</b>', reply_markup=sniffs_markup, parse_mode='HTML')
        return
    

    if d.startswith('sniff_'):
        hash_to_stop = d.split('sniff_')[1]
        target_username = await database.get_username(hash_to_stop)
        deleted = await database.delete_sniffing(hash_to_stop)

        back_to_stop_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='back', callback_data='back_to_stop')]
        ])

        if deleted:
            await call.message.edit_text(f'<b>Процесс слежки за @{target_username} был удалён.</b>', reply_markup=back_to_stop_kb, parse_mode='HTML')
        else:
            await call.message.edit_text(f'Не удалось удалить этот процесс.', reply_markup=back_to_stop_kb, parse_mode='HTML')
        return


    if d == 'back_to_stop':
        sniffs_text, sniffs_markup, total = await sniffer.get_sniffs_data(uid, page=1)
        if not sniffs_text:
            await call.message.edit_text('Процессов нет.')
            return

        await call.message.edit_text(f'<b>Твои процессы ({total}):</b>\n\n\n{sniffs_text}\n<b>Выбери процесс ниже:</b>', reply_markup=sniffs_markup, parse_mode='HTML')
        return


    if d == 'empty':
        await call.answer()
        return
    
    if d == 'delete_all_sniffs':
        await database.delete_all_sniffs()
        await call.message.edit_text(f'Все процессы были удалены.')


    await call.answer()


@dp.message(Form.wait_username)
async def username_waiting(message: Message, state: FSMContext):
    username = message.text
    uid = message.from_user.id
    
    if not username:
        await message.answer('Это не текст. Попробуй еще раз.', reply_markup=back_kb)
        await state.set_state(Form.wait_username)
        return

    if isinstance(username, str):
        sniff_exists = await database.check_sniff_exists(uid, username)
        if sniff_exists:
            await message.answer(f'Вы уже отслеживаете пользователя <b>{username}</b>.', parse_mode='HTML')
            await state.clear()
            return


        target_user_profile = None
        target_user_gifts = None


        try:
            target_user_profile = await client.get_chat(username)
        except (UsernameNotOccupied, UsernameInvalid, PhoneNotOccupied) as e:
            await message.answer('Такого пользователя нет.')
            await state.clear()
            return
        
        if target_user_profile.gift_count != None:
            try:
                target_user_gifts = [g async for g in client.get_chat_gifts(username)]
            except Exception as ee:
                print(f'Ошибка при получении списка подарков у {username} {e}')

        target_user_data = SniffingUser()
        target_user_data.profile = target_user_profile
        target_user_data.gifts = target_user_gifts
    
    else:
        await message.answer('Неверный формат. Попробуй еще раз.', reply_markup=back_kb)
        await state.set_state(Form.wait_username)
        return

    f = await sniffer.create_sniffing(uid, target_user_data)
    if f:
        await bot.send_chat_action(message.chat.id, 'typing')
        target_user = f'@{target_user_profile.username}' if target_user_profile.username else target_user_profile.id
        await message.answer(f'Процесс отслеживания пользователя <b>{target_user}</b> успешно начат.\nТы можешь просмотреть его во вкладке <b>Текущие процессы.</b>', parse_mode='HTML', reply_markup=start_kb)
        await state.clear()
        return
    else:
        await message.answer('Не удалось начать процесс.', reply_markup=back_kb)
        await state.clear()
        return


async def main():
    await database.init_db()
    await client.start()
    await sniffer.start()
    print('Started.')
    await dp.start_polling(bot)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
