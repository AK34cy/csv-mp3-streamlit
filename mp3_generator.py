# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from db import get_file
from mp3_builder import build_merged_mp3  # твоя функция генерации mp3

def mp3_generator_block(user):
    st.subheader("🎧 Генератор MP3")

    conn = st.session_state.conn

    if "current_file_id" not in st.session_state:
        st.info("Сначала выберите файл слева")
        return

    file_data = get_file(conn, st.session_state.current_file_id, user["id"])
    if not file_data:
        st.error("Файл не найден")
        return

    file_name = file_data['filename']
    df = pd.read_csv(BytesIO(file_data['data']), header=None).dropna(how="any").reset_index(drop=True)

    st.write(f"Выбран файл: **{file_name}** ({len(df)} строк)")

    # Параметры генерации
    pause_sec = st.slider("Пауза перед русским словом (кроме первого), сек", 0.0, 5.0, 0.5, 0.1)

    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация..."):
            mp3_buf = build_merged_mp3(df, pause_sec=pause_sec)
            st.audio(mp3_buf, format="audio/mp3")
            st.download_button("💾 Скачать MP3", data=mp3_buf, file_name=f"{file_name}.mp3")
