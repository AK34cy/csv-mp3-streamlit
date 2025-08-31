import streamlit as st
from auth import login_block
from file_manager import file_manager_block
from mp3_generator import mp3_generator_block

st.set_page_config(page_title="CSV → MP3", layout="wide")

def main():
    # Авторизация
    user = login_block()
    if not user:
        st.stop()

    st.sidebar.write(f"Привет, {user['name']} 👋")

    # Основное меню
    menu = st.sidebar.radio("Меню", ["Файлы", "Генератор MP3"])

    if menu == "Файлы":
        file_manager_block(user)

    elif menu == "Генератор MP3":
        mp3_generator_block(user)


if __name__ == "__main__":
    main()
