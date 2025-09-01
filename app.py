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

# --- инициализация соединения с БД ---
if "conn" not in st.session_state:
    try:
        conn = get_conn()
        init_db(conn)
        st.session_state.conn = conn
    except Exception as e:
        st.error(f"Ошибка подключения к БД: {e}")
        st.stop()

def main():
    # Авторизация
    if "user" not in st.session_state or st.session_state.user is None:
        user = login_block()
        if not user:
            return
    else:
        user = st.session_state.user

    # Левая колонка: имя, email, кнопка выйти + работа с файлами
    with st.sidebar:
        st.markdown(f"**Пользователь:** {user.get('name') or ''} ({user['email']})")
        if st.button("Выйти"):
            st.session_state.user = None
            st.experimental_rerun()

        # Работа с файлами
        file_manager_block(user)

    # Правый блок
    st.header("Основной блок")
    action = st.radio("Раздел", ["Генератор MP3", "Другой функционал"], index=0)

    if action == "Генератор MP3":
        from db import get_file   # импорт прямо перед использованием
        mp3_generator_block(user)
    else:
        st.info("Выберите раздел")

if __name__ == "__main__":
    main()
