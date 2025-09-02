# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from gtts import gTTS
from pydub import AudioSegment

def build_merged_mp3(df, selected_indices, pause_sec=0.5):
    """
    Генерация MP3 из DataFrame для выбранных строк.
    Каждая строка df превращается в звук, пауза между строками = pause_sec секунд.
    Русские слова озвучиваются на 'ru', немецкие на 'de'.
    """
    mp3_combined = AudioSegment.silent(duration=0)
    total = len(selected_indices)

    for idx, i in enumerate(selected_indices, 1):
        row = df.iloc[i]
        row_texts = [str(x) for x in row if pd.notna(x)]
        for text in row_texts:
            lang = "ru" if is_russian(text) else "de"
            tts = gTTS(text=text, lang=lang)
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            segment = AudioSegment.from_file(buf, format="mp3")
            mp3_combined += segment + AudioSegment.silent(duration=int(pause_sec * 1000))
        st.progress(idx / total)

    out_buf = BytesIO()
    mp3_combined.export(out_buf, format="mp3")
    out_buf.seek(0)
    return out_buf

def is_russian(text: str) -> bool:
    """Простая проверка: если есть кириллица, считаем русским"""
    return any('а' <= c <= 'я' or 'А' <= c <= 'Я' for c in text)

def mp3_generator_block(user, df, pause_sec, selected_indices):
    """
    Streamlit-блок генерации MP3.
    df: полный DataFrame выбранного файла
    selected_indices: индексы выбранных строк
    """
    st.subheader("🎧 Генератор MP3")

    if not selected_indices:
        st.info("Сначала выберите строки для генерации")
        return

    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация..."):
            mp3_buf = build_merged_mp3(df, selected_indices, pause_sec=pause_sec)
            st.audio(mp3_buf, format="audio/mp3")
            st.download_button(
                "💾 Скачать MP3",
                data=mp3_buf,
                file_name="output.mp3"
            )
