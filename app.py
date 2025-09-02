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

# --- главный блок ---
def main():
    # --- Левый сайдбар ---
    with st.sidebar:
        if "user" not in st.session_state or st.session_state.user is None:
            # Форма авторизации
            user = login_block()  # возвращает dict пользователя или None
            if user:
                st.session_state.user = user
                st.experimental_rerun()
        else:
            user = st.session_state.user
            # Верхняя панель: имя, email, кнопка выхода
            st.markdown(f"**Пользователь:** {user.get('name') or '—'} ({user['email']})")
            if st.button("Выйти"):
                st.session_state.user = None
                st.session_state.current_file_id = None
                st.experimental_rerun()

            # Работа с файлами
            file_manager_block(user)

    # --- Правый фрейм / основной контент ---
    if "user" in st.session_state and st.session_state.user:
        user = st.session_state.user
        right_col = st.container()
        with right_col:
            current_file_id = st.session_state.get("current_file_id")
            if current_file_id:
                file_data = get_file(st.session_state.conn, current_file_id, user["id"])
                if file_data:
                    file_name = file_data['filename']
                    df = pd.read_csv(BytesIO(file_data['data']), header=None).dropna(how="any").reset_index(drop=True)
        
                    # --- Список слов + параметры генерации ---
                    pause_sec = render_word_list(file_name, df)
        
                    # Получаем выбранные строки
                    selected_indices = st.session_state.selected_rows.get(file_name, [])
        
                    # Генерация MP3
                    mp3_generator_block(user, df, pause_sec, selected_indices)
if __name__ == "__main__":
    main()
