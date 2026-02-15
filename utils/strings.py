import hmac
import hashlib
import pickle
from datetime import datetime
from pyrogram.types import Gift
from data import SniffingUser, tz, f


def get_gifts_diffs_data(user_hash: str, diffs) -> str:
    gifts_diffs_text = ''
    str_for_file = ''

    for gd in diffs.items():
        move_type = 'Скрылся' if gd[0] == 'hidden' else 'Показался'
        moved_gifts: list[Gift] = gd[1]
        for c, hd in enumerate(moved_gifts, 1):
            emoji = hd.sticker.emoji if hd.sticker else hd.model.sticker.emoji
            received_time = hd.date.strftime('%d.%m.%Y, %H:%M')

            sender = f'{f'<b>@{hd.sender.username}</b> ' if hd.sender.username else ''}' + f'{f'(<code>{hd.sender.id}</code>) ' if hd.sender.id else ''}' + f'{hd.sender.full_name if hd.sender.full_name else ''}' if hd.sender else ''
            sender = f'({sender})' if sender else ''
            slug = f' <b><a href="{hd.link}">{hd.name}</a></b>' or ''

            new_str = f'{move_type} {c}.{slug} {emoji} | {received_time} {sender}\n'
            gifts_diffs_text += new_str
            str_for_file += new_str + str(hd) + '\n\n\n'


    file_name = f'{user_hash}_gd.txt'
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(str_for_file)

    return gifts_diffs_text


def get_profile_diffs_text(diff, indent=0) -> str:
    result = []
    prefix = "  " * indent
    
    for key, value in diff.items():
        if isinstance(value, dict) and 'old' in value and 'new' in value:
            old_val = str(value['old'])[:100] if value['old'] is not None else 'None'
            new_val = str(value['new'])[:100] if value['new'] is not None else 'None'
            result.append(f"<b>{prefix}{key}</b>: {old_val} → {new_val}")
        elif isinstance(value, dict):
            result.append(f"<b>{prefix}{key}</b>:")
            result.append(get_profile_diffs_text(value, indent + 1))
    
    return "\n".join(result) if result else ""


def format_delta_time(seconds) -> str:
    minutes = seconds // 60
    hours = seconds // 3600
    days = seconds // 86400
    
    if seconds < 60:
        delta_str = f"{seconds}с. назад"
    elif seconds < 3600:
        delta_str = f"{minutes}м. {seconds % 60}с. назад"
    elif seconds < 86400:
        delta_str = f"{hours}ч. {(seconds % 3600) // 60}м. назад"
    else:
        delta_str = f"{days}д. {(seconds % 86400) // 3600}ч. {(seconds % 3600) // 60}м. назад"
    return delta_str


def get_date(now):
    if not now: 
        return None
    return datetime.fromtimestamp(now).astimezone(tz).strftime('%d.%m.%Y, %H:%M')


def get_user_hash(user_data: SniffingUser) -> str:
    now = datetime.now().timestamp()
    hash_key = str(now).encode()
    str_user_data = str(user_data)[::-1].encode()
    hash_value = hmac.new(hash_key, str_user_data, hashlib.sha256).hexdigest()[:16]
    return hash_value


def encrypt_user_data(user_data: SniffingUser) -> bytes:
    bytes_user_data = pickle.dumps(user_data)
    ecnrypted_user_data = f.encrypt(bytes_user_data)
    return ecnrypted_user_data


def decrypt_user_data(encrypted_data: bytes) -> SniffingUser:
    decrypted_bytes = f.decrypt(encrypted_data)
    user_data = pickle.loads(decrypted_bytes)
    return user_data