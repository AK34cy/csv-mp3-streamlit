# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from gtts import gTTS
from pydub import AudioSegment
import re
import time

# Определение языка
def detect_lang(text: str):
    if re.search(r'[А-Яа-я]', text):
        return 'ru'
    else:
        return 'de'

def build_merged_mp3(df: pd.DataFrame, pause_sec: float = 0.5):
    combined = AudioSegment.silent(duration=0)
    for row in df.itertuples(index=False):
        text = " ".join(str(x) for x in row if pd.notna(x))
        lang = detect_lang(text)
        tts = gTTS(text=text, lang=lang)
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        segment = AudioSegment.from_file(buf, format="mp3")
        combined += segment + AudioSegment.silent(duration=int(pause_sec*1000))
    out_buf = BytesIO()
    combined.export(out_buf, format="mp3")
    out_buf.seek(0)
    return out_buf

def mp3_generator_block(user, df: pd.DataFrame, pause_sec: float = 0.5):
    st.subheader("🎧 Генератор MP3")

    if df is None or df.empty:
        st.info("Сначала выберите файл слева")
        return

    if st.button("▶️ Сгенерировать MP3"):
        progress_text = st.empty()
        progress_bar = st.progress(0)

        combined = AudioSegment.silent(duration=0)
        total = len(df)

        for i, row in enumerate(df.itertuples(index=False)):
            text = " ".join(str(x) for x in row if pd.notna(x))
            lang = detect_lang(text)
            tts = gTTS(text=text, lang=lang)
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            segment = AudioSegment.from_file(buf, format="mp3")
            combined += segment + AudioSegment.silent(duration=int(pause_sec*1000))

            progress_bar.progress(int((i+1)/total*100))
            progress_text.text(f"Генерация {i+1}/{total} строк...")
            time.sleep(0.02)

        # Новый буфер для Streamlit
        mp3_buf = BytesIO()
        combined.export(mp3_buf, format="mp3")
        mp3_buf.seek(0)

        # Плеер
        st.success("Генерация завершена!")
        st.audio(mp3_buf, format="audio/mp3")

        # Новый буфер для скачивания
        download_buf = BytesIO(mp3_buf.getvalue())
        st.download_button("💾 Скачать MP3", data=download_buf, file_name="output.mp3")
