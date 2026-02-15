from pyrogram.types import User
from aiosqlite import connect as con
from datetime import datetime
from utils import get_user_hash, encrypt_user_data
from data import DB_NAME, SniffingUser


class Database:

    async def init_db(self):
        try:
            async with con(DB_NAME) as db:
                await db.execute('''CREATE TABLE IF NOT EXISTS bot_users
                                (id INTEGER PRIMARY KEY,
                                uid INTEGER NOT NULL UNIQUE,
                                unm TEXT,
                                ufn TEXT,
                                fmt INTEGER)
                                ''')
                
                await db.execute('''CREATE TABLE IF NOT EXISTS sniffs
                                (id INTEGER PRIMARY KEY,
                                 hash CHAR UNIQUE,
                                 initiator_id INTEGER,
                                 target_id INTEGER,
                                 target_full_name CHAR,
                                 target_username CHAR,
                                 user_data BLOB,
                                 checked_last_time INTEGER,
                                 start_time INTEGER)
                                ''')
        except Exception as e:
            print('Ошибка при инициализации базы данных.', e)
    

    async def update_sniff_visual_data(self, user_hash: str, full_name: str, username: str) -> None:
        async with con(DB_NAME) as db:
            now = int(datetime.now().timestamp())
            await db.execute('UPDATE sniffs SET checked_last_time = ?, target_full_name = ?, target_username = ? WHERE hash = ?', (now, full_name, username, user_hash))
            await db.commit()


    async def update_sniff_user_data(self, user_hash: str, new_data: bytes) -> None:
        async with con(DB_NAME) as db:
            await db.execute('UPDATE sniffs SET user_data = ? WHERE hash = ?', (new_data, user_hash))
            await db.commit()


    async def get_all_sniffs(self) -> list:
        try:
            async with con(DB_NAME) as db:
                m = await db.execute('SELECT * FROM sniffs')
                sniffs_list = await m.fetchall()
            return sniffs_list
        except Exception as e:
            print('Не удалось получить список всех процессов.', e)


    async def get_user_sniffs(self, initiator_id: str) -> list:
        try:
            async with con(DB_NAME) as db:
                m = await db.execute('SELECT hash, target_id, target_full_name, target_username, user_data, checked_last_time, start_time FROM sniffs WHERE initiator_id = ?', (initiator_id, ))
                sniffs_list = await m.fetchall()
            return sniffs_list
        except Exception as e:
            print(f'Не удалось получить список процессов ({initiator_id=}).', e)


    async def get_username(self, user_hash: str) -> str:
        async with con(DB_NAME) as db:
            m = await db.execute('SELECT target_username FROM sniffs WHERE hash = ?', (user_hash, ))
            username = await m.fetchone()
        return username[0]


    async def delete_sniffing(self, user_hash: str) -> bool:
        success = True
        try:
            async with con(DB_NAME) as db:
                await db.execute('DELETE FROM sniffs WHERE hash = ?', (user_hash, ))
                await db.commit()
        except Exception as e:
            success = False
            print(f'Не удалось удалить процесс у {user_hash}', e)

        return success


    async def delete_all_sniffs(self) -> None:
        async with con(DB_NAME) as db:
            await db.execute('DELETE FROM sniffs')
            await db.commit()


    async def add_sniffing(self, initiator_id: int, user_data: SniffingUser) -> None:
        user_hash = get_user_hash(user_data)
        start_time = int(datetime.now().timestamp())
        checked_last_time = start_time
        profile = user_data.profile
        user_id = profile.id
        user_full_name = profile.full_name
        username = profile.username
        enc_ud = encrypt_user_data(user_data)
        async with con(DB_NAME) as db:
            await db.execute('INSERT INTO sniffs VALUES(NULL, ?, ?, ?, ?, ?, ?, ?, ?)', (user_hash, initiator_id, user_id, user_full_name, username, enc_ud, checked_last_time, start_time, ))
            await db.commit()


    async def check_sniff_exists(self, initiator_id: int, target_id: int | str) -> bool:
        async with con(DB_NAME) as db:
            if isinstance(target_id, str) and not target_id.isdigit():
                m = await db.execute('SELECT 1 FROM sniffs WHERE initiator_id = ? AND LOWER(target_username) = LOWER(?) LIMIT 1',
                    (initiator_id, target_id))
            else:
                m = await db.execute('SELECT 1 FROM sniffs WHERE initiator_id = ? AND target_id = ? LIMIT 1',
                    (initiator_id, int(target_id)))
            
            result = await m.fetchone()
            return result is not None


    async def reg_user(self, user: User) -> None:
        try:
            uid = user.id
            unm = user.username
            ufn = user.full_name
            fmt = int(datetime.now().timestamp())
            async with con(DB_NAME) as db:
                await db.execute('INSERT OR IGNORE INTO bot_users VALUES(NULL, ?, ?, ?, ?)', (uid, unm, ufn, fmt,))
                await db.commit()
        except Exception as e:
            print('Ошибка при добавлении пользователя в бд.', e)