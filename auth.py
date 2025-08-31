import streamlit as st
import bcrypt
from db import get_user_by_email, create_user
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def login_block():
    st.header("Авторизация")

    # Если пользователь уже в сессии
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user

    tab_login, tab_register = st.tabs(["Вход", "Регистрация"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Пароль", type="password", key="login_password")

        if st.button("Войти"):
            user = get_user_by_email(st.session_state.conn, email.strip().lower())
            if not user:
                st.error("Пользователь не найден")
            else:
                if bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Неверный пароль")

    with tab_register:
        name = st.text_input("Имя", key="reg_name")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Пароль", type="password", key="reg_password")
        password_repeat = st.text_input("Повторите пароль", type="password", key="reg_password_repeat")

        if st.button("Зарегистрироваться"):
            email = email.strip().lower()
            if not EMAIL_RE.match(email):
                st.error("Некорректный email")
            elif len(password) < 6:
                st.error("Пароль должен быть не короче 6 символов")
            elif password != password_repeat:
                st.error("Пароли не совпадают")
            elif get_user_by_email(st.session_state.conn, email):
                st.error("Пользователь с таким email уже существует")
            else:
                pwd_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                user = create_user(st.session_state.conn, email, name.strip(), pwd_hash)
                st.session_state.user = user
                st.success("Регистрация успешна")
                st.rerun()

    return None
