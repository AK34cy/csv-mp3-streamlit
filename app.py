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
from mp3_generator import mp3_generator_block  # сюда можно добавить правый фрейм для списков слов

# --- инициализация соединения с БД ---
if "conn" not in st.session_state:
    try:
        conn = get_conn()
        init_db(conn)
        st.session_state.conn = conn
    except Exception as e:
        st.error(f"Ошибка подключения к БД: {e}")
        st.stop()

# --- проверка авторизации ---
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    # вызываем авторизацию
    st.session_state.user = login_block()

if st.session_state.user:
    user = st.session_state.user

    # --- Сайдбар (левый фрейм) ---
    st.sidebar.markdown(f"**Пользователь:** {user.get('name') or user['email']}")
    if st.sidebar.button("Выйти"):
        st.session_state.user = None
        st.experimental_rerun()

    st.sidebar.subheader("📂 Файлы")
    file_manager_block(user)  # левый фрейм, работа с файлами

    # --- Правый фрейм (основной) ---
    st.subheader("📖 Списки слов / другой контент")
    # Здесь можно разместить ваши списки слов или функционал генератора MP3
    mp3_generator_block(user)
