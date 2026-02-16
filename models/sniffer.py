import asyncio
from datetime import datetime
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from pyrogram.errors.exceptions import UsernameNotOccupied, PeerIdInvalid
from random import randint
from os import remove
from data import client, bot, SniffingUser
from models.database import Database
from utils import *


database = Database()


class Sniffer:
    
    def __init__(self):
        self.PROCESSING = True


    async def _start(self):
        while self.PROCESSING: 
            all_sniffs = await database.get_all_sniffs()
            if not all_sniffs:
                await asyncio.sleep(30)
                continue
        
            sorted_sniffs = sorted(all_sniffs, key=lambda x: x[7] or x[8])
            for sniff in sorted_sniffs:
                user_hash = sniff[1]
                user_id = sniff[3]
                initiator_id = sniff[2]
                username = sniff[5]
                encrypted_user_data = (sniff[6])
                old_user_data = decrypt_user_data(encrypted_user_data)

                try:
                    while True: #костыль уровень mr robot (случай когда тот кого отслеживаем поменял юз, надо искать по айди тк юз уже другой)
                        peer = username
                        try:
                            now_user_profile = await client.get_chat(peer)
                            break
                        except (UsernameNotOccupied, PeerIdInvalid) as e:
                            peer = user_id
                            continue


                    now_user_gifts = [x async for x in client.get_chat_gifts(user_id)]
                    await database.update_sniff_visual_data(user_hash, now_user_profile.full_name, now_user_profile.username)


                    now_user_data = SniffingUser()
                    now_user_data.profile = now_user_profile
                    now_user_data.gifts = now_user_gifts


                    profile_diffs, gifts_diffs = get_user_diffs(old_user_data, now_user_data)


                    sniff_exists = await database.check_sniff_exists(initiator_id, user_id)
                    if sniff_exists:
                        if gifts_diffs['exists']:
                            gifts_diffs.pop('exists')
                            gifts_diffs_text = get_gifts_diffs_data(user_hash, gifts_diffs)

                            await bot.send_message(chat_id=initiator_id, text=f'<b>Изменения в подарках у пользователя @{username}!</b>', parse_mode='HTML')
                            if len(gifts_diffs_text) >= 4096:
                                for i in range(0, len(gifts_diffs_text), 4096):
                                    text = gifts_diffs_text[i:i+4096]
                                    await bot.send_message(chat_id=initiator_id, text=text, parse_mode='HTML', disable_web_page_preview=True)
                            else:
                                await bot.send_message(chat_id=initiator_id, text=gifts_diffs_text, parse_mode='HTML', disable_web_page_preview=True)

                            file_name = f'{user_hash}_gd.txt'
                            document = FSInputFile(file_name)
                            await bot.send_document(chat_id=initiator_id, document=document)
                            remove(file_name)


                        if profile_diffs:
                            profile_diffs_text = get_profile_diffs_text(profile_diffs)

                            await bot.send_message(chat_id=initiator_id, text=f'<b>Изменения в профиле у пользователя @{username}!</b>', parse_mode='HTML')
                            await bot.send_message(chat_id=initiator_id, text=profile_diffs_text, parse_mode='HTML')
                        

                        encrypted_now_user_data = encrypt_user_data(now_user_data)
                        await database.update_sniff_user_data(user_hash, encrypted_now_user_data)


                except Exception as e:
                    print(f'Ошибка при отслеживании {user_id} | {username} {user_hash=}. {e}',)
                    continue

                await asyncio.sleep(randint(5,15))
                continue


    async def start(self) -> None:
        self.main_task = asyncio.create_task(self._start()) 
        return self.main_task


    async def create_sniffing(self, initiator_id: int, user_data: SniffingUser) -> bool:
        success = True
        
        try:
            await database.add_sniffing(initiator_id, user_data)
        except Exception as e:
            print('Ошибка при создании процесса.', e)
            success = False

        return success
    

    async def get_sniffs_data(self, uid: int, page: int = 1) -> tuple:
        sniffs_list = await database.get_user_sniffs(uid)
        if not sniffs_list:
            return None, None, None

        total = len(sniffs_list)
        per_page = 9
        total_pages = (total + per_page - 1) // per_page
        page = max(1, min(page, total_pages))

        start = (page - 1) * per_page
        current_sniffs = sniffs_list[start:start + per_page]

        sniffs_text = ''
        for i, sniff in enumerate(current_sniffs, start + 1):
            user_id = sniff[1]
            username = sniff[3]
            checked_last_time = sniff[5]
            sniff_start_time = sniff[6]

            username = f'@{username}' if username else 'без имени'
            start_date = get_date(sniff_start_time)
            last_date = get_date(checked_last_time) if checked_last_time else 'нет'
            delta = format_delta_time(int(datetime.now().timestamp() - sniff_start_time))

            sniffs_text += f'{i}. <b>{username}</b> (<code>{user_id}</code>) | Начало: {start_date} ({delta}) | Последняя сверка: {last_date}\n\n'

        markup = [[] for _ in range((len(current_sniffs) + 2) // 3)]

        for i, sniff in enumerate(current_sniffs, 1):
            row = (i - 1) // 3
            markup[row].append(InlineKeyboardButton(
                text=str((start + i) if page > 1 else i),
                callback_data=f'sniff_{sniff[0]}'
            ))

        if total > 1:
            markup.append([InlineKeyboardButton(text='Удалить все процессы', callback_data='delete_all_sniffs', style='danger')])

        if total_pages > 1:
            nav = []
            nav.append(InlineKeyboardButton(
                text='⬅️' if page > 1 else ' ',
                callback_data=f'page_{page-1}' if page > 1 else 'empty'
            ))
            nav.append(InlineKeyboardButton(
                text=f'{page}/{total_pages}',
                callback_data='empty'
            ))
            nav.append(InlineKeyboardButton(
                text='➡️' if page < total_pages else ' ',
                callback_data=f'page_{page+1}' if page < total_pages else 'empty'
            ))
            markup.append(nav)

        return sniffs_text, InlineKeyboardMarkup(inline_keyboard=markup), total

