# app.py
import streamlit as st
from io import BytesIO
import pandas as pd
from dotenv import load_dotenv

# локальные модули
from db import get_conn, init_db, get_file
from sidebar_ui import render_sidebar       # левый сайдбар
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
        if "user" not in st.session_state or st.session_state.user is None:
            return  # если пользователь не авторизован — выходим

    # --- Правый фрейм / основной контент ---
    user = st.session_state.user
    right_col = st.container()
    with right_col:
        current_file_id = st.session_state.get("current_file_id")
        if current_file_id:
            file_data = get_file(st.session_state.conn, current_file_id, user["id"])
            if file_data:
                file_name = file_data['filename']
                file_lang = file_data.get('lang', 'de')  # язык файла из БД, по умолчанию "de"
                df = pd.read_csv(BytesIO(file_data['data']), header=None).dropna(how="any").reset_index(drop=True)

                # Список слов + параметры генерации
                pause_sec, selected_indices = render_word_list(file_name, df)

                # Генерация MP3 по выбранным строкам
                selected_rows = df.iloc[selected_indices].values.tolist() if selected_indices else []
                mp3_generator_block(user, selected_rows, pause_ms=int(pause_sec * 1000), file_lang=file_lang)

if __name__ == "__main__":
    main()
