import re
import bcrypt
from db import get_user_by_email, create_user

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def register_user(conn, email: str, name: str, password: str, password_repeat: str):
    """
    Возвращает (ok: bool, msg: str, user: dict|None)
    """
    email = (email or "").strip().lower()
    name = (name or "").strip()

    if not EMAIL_RE.match(email):
        return False, "Некорректный email", None
    if len(password) < 6:
        return False, "Пароль должен быть не короче 6 символов", None
    if password != password_repeat:
        return False, "Пароли не совпадают", None

    exists = get_user_by_email(conn, email)
    if exists:
        return False, "Пользователь с таким email уже существует", None

    pwd_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = create_user(conn, email=email, name=name, password_hash=pwd_hash)
    return True, "Регистрация успешна", user
