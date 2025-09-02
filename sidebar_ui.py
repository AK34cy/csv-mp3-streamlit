# sidebar_ui.py
import streamlit as st
from auth import login_block
from file_manager import file_manager_block

def render_sidebar():
    """
    Отрисовка левого сайдбара.
    До авторизации — форма логина.
    После авторизации — имя, email, кнопка выхода и работа с файлами.
    """
    if "user" not in st.session_state or st.session_state.user is None:
        # Форма авторизации
        user = login_block()
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
