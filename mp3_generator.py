import streamlit as st
import pandas as pd
from io import BytesIO
from db import get_file
from gtts import gTTS
from pydub import AudioSegment
import re

RE_RU = re.compile(r'[а-яА-ЯёЁ]')
RE_DE = re.compile(r'[a-zA-ZäöüßÄÖÜ]')

def detect_lang(text: str) -> str:
    if RE_RU.search(text):
        return 'ru'
    elif RE_DE.search(text):
        return 'de'
    return 'ru'

def build_merged_mp3(df: pd.DataFrame, pause_sec: float = 0.5, progress_callback=None) -> BytesIO:
    mp3_combined = AudioSegment.silent(duration=0)
    total_rows = len(df)

    for idx, row in enumerate(df.itertuples(index=False), 1):
        text = " ".join(str(x) for x in row if pd.notna(x))
        lang = detect_lang(text)
        tts = gTTS(text=text, lang=lang)
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        segment = AudioSegment.from_file(buf, format="mp3")
        mp3_combined += segment + AudioSegment.silent(duration=int(pause_sec * 1000))
        if progress_callback:
            progress_callback(idx, total_rows)

    out_buf = BytesIO()
    mp3_combined.export(out_buf, format="mp3")
    out_buf.seek(0)
    return out_buf

def mp3_generator_block(user, df: pd.DataFrame, pause_sec: float = 0.5):
    st.subheader("🎧 Генератор MP3")
    if df.empty:
        st.info("Сначала выберите файл слева")
        return

    if "generate_mp3" not in st.session_state:
        st.session_state.generate_mp3 = False

    # Кнопка запуска
    if st.button("▶️ Сгенерировать MP3"):
        st.session_state.generate_mp3 = True

    if st.session_state.generate_mp3:
        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_cb(idx, total):
            progress_bar.progress(idx / total)
            status_text.text(f"Генерация: строка {idx}/{total}")

        mp3_buf = build_merged_mp3(df, pause_sec=pause_sec, progress_callback=progress_cb)

        st.audio(mp3_buf, format="audio/mp3")
        st.download_button("💾 Скачать MP3", data=mp3_buf, file_name="output.mp3")

        status_text.empty()
        progress_bar.empty()
        st.session_state.generate_mp3 = False
