# app.py
import streamlit as st
from io import BytesIO
import pandas as pd
from dotenv import load_dotenv

# локальные модули
from db import get_conn, init_db, get_file
from auth import login_block
from file_manager import file_manager_block
from mp3_generator import mp3_generator_block
from word_list_ui import render_word_list

# --- инициализация конфигов ---
load_dotenv()
st.set_page_config(page_title="CSV → MP3", layout="wide")

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
    # Левый и правый фреймы
    left_col, right_col = st.columns([1, 2])

    with left_col:
        user = st.session_state.get("user")

        if user:
            # Пользователь вошёл — показываем имя, email и кнопку выхода
            st.markdown(f"**Пользователь:** {user.get('name') or '—'} ({user['email']})")
            if st.button("Выйти"):
                st.session_state.user = None
                st.session_state.current_file_id = None
                st.experimental_rerun()
        else:
            # Пользователь не вошёл — показываем форму авторизации
            user = login_block()
            if user:
                st.session_state.user = user
                st.experimental_rerun()

        # Работа с файлами доступна только после авторизации
        if user:
            file_manager_block(user)

    with right_col:
        user = st.session_state.get("user")
        if user and "current_file_id" in st.session_state:
            file_data = get_file(st.session_state.conn, st.session_state.current_file_id, user["id"])
            if file_data:
                file_name = file_data['filename']
                df = pd.read_csv(BytesIO(file_data['data']), header=None).dropna(how="any").reset_index(drop=True)

                # Список слов + параметры генерации
                pause_sec = render_word_list(file_name, df)

                # Генерация MP3
                mp3_generator_block(user, df, pause_sec)

if __name__ == "__main__":
    main()
