# auth.py
import re
import bcrypt
import streamlit as st
from db import get_user_by_email, create_user

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def login_block():
    """Возвращает user dict или None после авторизации/регистрации"""
    st.sidebar.subheader("🔑 Авторизация")
    conn = st.session_state.conn

    if "user" not in st.session_state:
        st.session_state.user = None

    tab_login, tab_reg = st.sidebar.tabs(["Войти", "Регистрация"])

    user = None
    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Пароль", type="password", key="login_pwd")
        if st.button("Войти"):
            if email and password:
                u = get_user_by_email(conn, email.strip().lower())
                if u and bcrypt.checkpw(password.encode("utf-8"), u["password_hash"].encode("utf-8")):
                    st.session_state.user = u
                    st.success(f"Добро пожаловать, {u.get('name') or u['email']}!")
                    st.experimental_rerun()
                else:
                    st.error("Неверный email или пароль")
    
    with tab_reg:
        email = st.text_input("Email", key="reg_email")
        name = st.text_input("Имя", key="reg_name")
        password = st.text_input("Пароль", type="password", key="reg_pwd")
        password_repeat = st.text_input("Повтор пароля", type="password", key="reg_pwd2")
        if st.button("Зарегистрироваться"):
            ok, msg, user = register_user(conn, email, name, password, password_repeat)
            if ok:
                st.session_state.user = user
                st.success(msg)
                st.experimental_rerun()
            else:
                st.error(msg)

    return st.session_state.user


def register_user(conn, email: str, name: str, password: str, password_repeat: str):
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
