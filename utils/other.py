from pyrogram.types import Gift
from data import SniffingUser


def get_gifts_diffs(old_gifts: list[Gift] | None, new_gifts: list[Gift] | None) -> dict[str, list[Gift]]:
    old_gifts = old_gifts or []
    new_gifts = new_gifts or []
    
    if not old_gifts and not new_gifts:
        return {'hidden': [], 'shown': [], 'exists': False}
    
    try:
        old_ids = {gift.id for gift in old_gifts}
        new_ids = {gift.id for gift in new_gifts}
        
        hidden = [gift for gift in old_gifts if gift.id not in new_ids]
        shown = [gift for gift in new_gifts if gift.id not in old_ids]
        
    except (AttributeError, TypeError):
        old_set = set(old_gifts)
        new_set = set(new_gifts)
        
        hidden = [gift for gift in old_gifts if gift not in new_set]
        shown = [gift for gift in new_gifts if gift not in old_set]
    
    return {
        'hidden': hidden,
        'shown': shown,
        'exists': bool(hidden or shown)
    }


def get_profile_diffs(dict1, dict2, depth=5):
    dict1, dict2 = dict1.__dict__, dict2.__dict__
    diff = {}

    for key in set(dict1.keys()) | set(dict2.keys()):
        val1 = dict1.get(key)
        val2 = dict2.get(key)
        
        if val1 != val2:
            if val1 is None and val2 is None:
                continue
                
            if depth > 0 and hasattr(val1, '__dict__') and hasattr(val2, '__dict__'):
                nested_diff = get_profile_diffs(val1, val2, depth-1)
                if nested_diff:
                    diff[key] = nested_diff
            else:
                diff[key] = {'old': val1, 'new': val2}
    
    remove_unacceptable_keys(diff)
    return diff


def get_user_diffs(old_user_data: SniffingUser, now_user_data: SniffingUser):
    old_user_profile = old_user_data.profile
    now_user_profile = now_user_data.profile
    profile_diffs = get_profile_diffs(old_user_profile, now_user_profile)


    old_user_gifts = old_user_data.gifts
    now_user_gifts = now_user_data.gifts
    gifts_diffs = get_gifts_diffs(old_user_gifts, now_user_gifts)

    return profile_diffs, gifts_diffs


def remove_unacceptable_keys(diff_dict, parent_key=None):
    keys_to_remove = []
    
    for key, value in list(diff_dict.items()):
        if key == 'raw' or key == '_client':
            keys_to_remove.append(key)
            continue
            
        if parent_key == 'business_intro' and key == 'sticker':
            if isinstance(value, dict):
                sticker_keys_to_remove = []
                for sticker_key in value.keys():
                    if sticker_key in {'thumbs', 'file_id', 'raw'}:
                        sticker_keys_to_remove.append(sticker_key)
                for sk in sticker_keys_to_remove:
                    value.pop(sk, None)
                if not value:
                    keys_to_remove.append(key)
                    
        elif key == 'first_profile_audio':
            if isinstance(value, dict):
                audio_keys_to_remove = []
                for audio_key in value.keys():
                    if audio_key in {'thumbs', 'file_id'}:
                        audio_keys_to_remove.append(audio_key)
                for ak in audio_keys_to_remove:
                    value.pop(ak, None)
                if not value:
                    keys_to_remove.append(key)
        
        if isinstance(value, dict):
            remove_unacceptable_keys(value, key)
            if not value:
                keys_to_remove.append(key)
    
    for key in keys_to_remove:
        diff_dict.pop(key, None)
