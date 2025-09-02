# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from db import get_file
from gtts import gTTS
from pydub import AudioSegment

def build_merged_mp3(df, selected_indices=None, pause_sec=0.5):
    """
    Генерация MP3 из DataFrame.
    selected_indices: список индексов строк для генерации
    pause_sec: пауза между строками в секундах
    """
    if selected_indices is None:
        selected_indices = df.index.tolist()

    mp3_combined = AudioSegment.silent(duration=0)
    for i in selected_indices:
        row = df.iloc[i]
        text_ru = []
        text_de = []

        # Разделяем по языкам (русский / немецкий) по индексу столбца
        for idx, cell in enumerate(row):
            if pd.isna(cell):
                continue
            # Если столбец четный — русское слово, нечетный — немецкое
            if idx % 2 == 0:
                text_ru.append(str(cell))
            else:
                text_de.append(str(cell))

        # Генерация русского MP3
        if text_ru:
            tts_ru = gTTS(text=" ".join(text_ru), lang="ru")
            buf_ru = BytesIO()
            tts_ru.write_to_fp(buf_ru)
            buf_ru.seek(0)
            seg_ru = AudioSegment.from_file(buf_ru, format="mp3")
            mp3_combined += seg_ru + AudioSegment.silent(duration=int(pause_sec*1000))

        # Генерация немецкого MP3
        if text_de:
            tts_de = gTTS(text=" ".join(text_de), lang="de")
            buf_de = BytesIO()
            tts_de.write_to_fp(buf_de)
            buf_de.seek(0)
            seg_de = AudioSegment.from_file(buf_de, format="mp3")
            mp3_combined += seg_de + AudioSegment.silent(duration=int(pause_sec*1000))

    out_buf = BytesIO()
    mp3_combined.export(out_buf, format="mp3")
    out_buf.seek(0)
    return out_buf

def mp3_generator_block(user, df, pause_sec, selected_indices):
    """
    Streamlit-блок генерации MP3.
    df: DataFrame выбранного файла
    pause_sec: пауза между строками
    selected_indices: список индексов выбранных строк
    """
    st.subheader("🎧 Генератор MP3")
    file_name = st.session_state.get("current_file_name", "output")

    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация..."):
            mp3_buf = build_merged_mp3(df, selected_indices, pause_sec=pause_sec)
            st.audio(mp3_buf, format="audio/mp3")
            st.download_button(
                "💾 Скачать MP3",
                data=mp3_buf,
                file_name=f"{file_name}.mp3"
            )
