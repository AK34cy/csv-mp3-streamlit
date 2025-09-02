# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from db import get_file
from gtts import gTTS
from pydub import AudioSegment

def build_merged_mp3(df, pause_sec=0.5):
    """
    Генерация MP3 из DataFrame с паузой между строками.
    Каждая строка определяется по языку: русские слова - ru, немецкие - de.
    """
    mp3_combined = AudioSegment.silent(duration=0)
    n = len(df)
    progress_bar = st.progress(0)

    for i, row in enumerate(df.itertuples(index=False), 1):
        text = " ".join(str(x) for x in row if pd.notna(x))
        # Определяем язык
        lang = 'ru' if any('А' <= c <= 'я' for c in text) else 'de'
        tts_buf = BytesIO()
        tts = gTTS(text=text, lang=lang)
        tts.write_to_fp(tts_buf)
        tts_buf.seek(0)
        segment = AudioSegment.from_file(tts_buf, format="mp3")
        mp3_combined += segment + AudioSegment.silent(duration=int(pause_sec * 1000))
        progress_bar.progress(i / n)

    out_buf = BytesIO()
    mp3_combined.export(out_buf, format="mp3")
    out_buf.seek(0)
    return out_buf

def mp3_generator_block(user, df, pause_sec=0.5):
    """
    Streamlit-блок генерации MP3.
    df - DataFrame выбранного файла.
    pause_sec - пауза между строками.
    """
    st.subheader("🎧 Генератор MP3")
    if df is None or df.empty:
        st.info("Сначала выберите файл")
        return

    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация..."):
            mp3_buf = build_merged_mp3(df, pause_sec)
            st.audio(mp3_buf, format="audio/mp3")
            st.download_button("💾 Скачать MP3", data=mp3_buf, file_name="output.mp3")
