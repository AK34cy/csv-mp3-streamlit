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
    user = login_block()
    if not user:
        return

    st.session_state.user = user

    # --- Левый и правый фреймы ---
    left_col, right_col = st.columns([1, 2])

    with left_col:
        # Верхняя панель: имя, email, кнопка выхода
        st.markdown(f"**Пользователь:** {user.get('name') or '—'} ({user['email']})")
        if st.button("Выйти"):
            st.session_state.user = None
            st.experimental_rerun()

        # Работа с файлами
        file_manager_block(user)

    with right_col:
        # Если выбран файл, показываем его данные
        current_file_id = st.session_state.get("current_file_id")
        if current_file_id:
            file_data = get_file(st.session_state.conn, current_file_id, user["id"])
            if file_data:
                file_name = file_data['filename']
                df_full = pd.read_csv(BytesIO(file_data['data']), header=None).dropna(how="any").reset_index(drop=True)

                # --- Блок списка слов + выбор строк ---
                selected_indices, pause_sec = render_word_list(file_name, df_full)

                # --- Создаем df только с выбранными строками ---
                df_selected = df_full.loc[selected_indices] if selected_indices else pd.DataFrame()

                # --- Генерация MP3 ---
                mp3_generator_block(user, df_selected, pause_sec)

if __name__ == "__main__":
    main()
