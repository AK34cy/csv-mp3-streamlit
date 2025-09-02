# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from db import get_file
from gtts import gTTS
from pydub import AudioSegment
import re

# Регулярки для определения языка
RE_RU = re.compile(r'[а-яА-ЯёЁ]')
RE_DE = re.compile(r'[a-zA-ZäöüßÄÖÜ]')  # базовые буквы немецкого

def detect_lang(text: str) -> str:
    """Определяем язык строки: 'ru' или 'de'"""
    if RE_RU.search(text):
        return 'ru'
    elif RE_DE.search(text):
        return 'de'
    return 'ru'  # по умолчанию русская озвучка

def build_merged_mp3(df: pd.DataFrame, pause_sec: float = 0.5) -> BytesIO:
    """
    Генерация MP3 из DataFrame.
    Каждая строка df превращается в звук с паузой pause_sec между строками.
    Автоопределение языка для каждой строки.
    """
    mp3_combined = AudioSegment.silent(duration=0)
    for row in df.itertuples(index=False):
        text = " ".join(str(x) for x in row if pd.notna(x))
        lang = detect_lang(text)
        tts = gTTS(text=text, lang=lang)
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        segment = AudioSegment.from_file(buf, format="mp3")
        mp3_combined += segment + AudioSegment.silent(duration=int(pause_sec * 1000))
    out_buf = BytesIO()
    mp3_combined.export(out_buf, format="mp3")
    out_buf.seek(0)
    return out_buf

def mp3_generator_block(user, df: pd.DataFrame, pause_sec: float = 0.5):
    """
    Streamlit-блок генерации MP3 с прогресс-баром и автоопределением языка.
    """
    st.subheader("🎧 Генератор MP3")
    if df.empty:
        st.info("Сначала выберите файл слева")
        return

    total_rows = len(df)
    mp3_combined = AudioSegment.silent(duration=0)

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, row in enumerate(df.itertuples(index=False), 1):
        text = " ".join(str(x) for x in row if pd.notna(x))
        lang = detect_lang(text)
        tts = gTTS(text=text, lang=lang)
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        segment = AudioSegment.from_file(buf, format="mp3")
        mp3_combined += segment + AudioSegment.silent(duration=int(pause_sec * 1000))

        progress_bar.progress(idx / total_rows)
        status_text.text(f"Генерация: строка {idx}/{total_rows}")

    out_buf = BytesIO()
    mp3_combined.export(out_buf, format="mp3")
    out_buf.seek(0)

    st.audio(out_buf, format="audio/mp3")
    st.download_button("💾 Скачать MP3", data=out_buf, file_name="output.mp3")
    status_text.empty()
    progress_bar.empty()
