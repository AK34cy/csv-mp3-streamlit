# app.py
import streamlit as st
from dotenv import load_dotenv
import os

# инициализация конфигов
load_dotenv()
st.set_page_config(page_title="CSV → MP3", layout="wide")

# локальные модули
from db import get_conn, init_db
from auth import login_block
from file_manager import file_manager_block
from mp3_generator import mp3_generator_block

# --- инициализация соединения с БД (помещаем в session_state) ---
if "conn" not in st.session_state:
    try:
        conn = get_conn()
        init_db(conn)
        st.session_state.conn = conn
    except Exception as e:
        st.error(f"Ошибка подключения к БД: {e}")
        st.stop()

def main():
    # 1) Авторизация (возвращает user dict или None)
    user = login_block()
    if not user:
        # login_block сам вызывает st.stop() при необходимости, но на всякий случай:
        return

    st.sidebar.markdown(f"**Пользователь:** {user.get('name') or user['email']}")
    action = st.sidebar.radio("Раздел", ["Файлы", "Генератор MP3", "Выйти"])

    if action == "Файлы":
        file_manager_block(user)        # берет st.session_state.conn внутри
    elif action == "Генератор MP3":
        mp3_generator_block(user)       # берет st.session_state.conn внутри
    else:  # Выйти
        st.session_state.user = None
        st.experimental_rerun()

if __name__ == "__main__":
    main()
