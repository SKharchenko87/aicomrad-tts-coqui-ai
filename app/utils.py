from typing import List

def split_text(text: str, max_len: int = 900) -> List[str]:
    """
    Простая логика разбиения: по предложениям, либо по пробелам.
    Разбивает текст на части, не превышающие max_len символов.
    """
    if len(text) <= max_len:
        return [text]

    parts = []
    cur = ''
    for token in text.split(' '):
        if len(cur) + len(token) + 1 > max_len:
            parts.append(cur.strip())
            cur = token
        else:
            cur = (cur + ' ' + token).strip()
    if cur:
        parts.append(cur.strip())
    return parts
