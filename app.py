# app.py
import streamlit as st
from io import BytesIO
import pandas as pd
from dotenv import load_dotenv

# локальные модули
from db import get_conn, init_db, get_file
from sidebar_ui import render_sidebar
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
        render_sidebar()
    user = sidebar_block()  # sidebar_block сам сохраняет пользователя в session_state
    if not user:
        return

    # --- Правый фрейм / основной контент ---
    right_col = st.container()
    with right_col:
        current_file_id = st.session_state.get("current_file_id")
        if current_file_id:
            file_data = get_file(st.session_state.conn, current_file_id, user["id"])
            if file_data:
                file_name = file_data['filename']
                df = pd.read_csv(BytesIO(file_data['data']), header=None).dropna(how="any").reset_index(drop=True)

                # --- Список слов и выбранные индексы ---
                pause_sec, selected_indices = render_word_list(file_name, df)

                # --- Генерация MP3 по выбранным строкам ---
                if selected_indices:
                    selected_df = df.loc[selected_indices].reset_index(drop=True)
                    mp3_generator_block(user, selected_df, pause_sec)
                else:
                    st.info("Сначала выберите строки для генерации")

if __name__ == "__main__":
    main()
