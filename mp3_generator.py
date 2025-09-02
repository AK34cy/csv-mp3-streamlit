# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from db import get_file
from gtts import gTTS
from pydub import AudioSegment
import time

def build_merged_mp3(df, pause_sec=0.5):
    """
    Генерация MP3 из DataFrame с паузой между строками.
    Автоматически определяет язык: русские слова -> 'ru', немецкие -> 'de'
    """
    mp3_combined = AudioSegment.silent(duration=0)
    total = len(df)
    progress_bar = st.progress(0)
    
    for idx, row in enumerate(df.itertuples(index=False), 1):
        text_parts = [str(x) for x in row if pd.notna(x)]
        if not text_parts:
            continue

        # Определение языка каждой части (русская / немецкая)
        audio_segments = []
        for part in text_parts:
            lang = 'de' if any('a' <= c.lower() <= 'z' for c in part) else 'ru'
            tts = gTTS(text=part, lang=lang)
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            segment = AudioSegment.from_file(buf, format="mp3")
            audio_segments.append(segment)
            audio_segments.append(AudioSegment.silent(duration=int(pause_sec*1000)))

        # Объединяем все сегменты строки
        for seg in audio_segments:
            mp3_combined += seg

        progress_bar.progress(idx / total)

    out_buf = BytesIO()
    mp3_combined.export(out_buf, format="mp3")
    out_buf.seek(0)
    return out_buf

def mp3_generator_block(user, df, pause_sec=0.5):
    """
    Streamlit-блок генерации MP3.
    df уже должен содержать только выбранные пользователем строки.
    """
    st.subheader("🎧 Генератор MP3")

    if df.empty:
        st.info("Нет выбранных строк для генерации")
        return

    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация MP3..."):
            mp3_buf = build_merged_mp3(df, pause_sec=pause_sec)
            st.audio(mp3_buf, format="audio/mp3")
            st.download_button(
                "💾 Скачать MP3",
                data=mp3_buf,
                file_name="output.mp3"
            )
