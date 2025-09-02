# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from db import get_file
from gtts import gTTS
from pydub import AudioSegment
import re
import time

# Простейшее определение языка по символам: кириллица -> русский, латиница -> немецкий
def detect_lang(text: str):
    if re.search(r'[А-Яа-я]', text):
        return 'ru'
    else:
        return 'de'

def build_merged_mp3(df: pd.DataFrame, pause_sec: float = 0.5):
    """
    Генерация MP3 из DataFrame.
    Каждая строка df превращается в звук, пауза между строками = pause_sec секунд.
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
    Streamlit-блок генерации MP3.
    df: DataFrame выбранного файла
    pause_sec: пауза между строками
    """
    st.subheader("🎧 Генератор MP3")

    if df is None or df.empty:
        st.info("Сначала выберите файл слева")
        return

    # Кнопка генерации с прогресс-баром
    if st.button("▶️ Сгенерировать MP3"):
        progress_text = st.empty()
        progress_bar = st.progress(0)

        mp3_combined = BytesIO()
        total_rows = len(df)
        temp_audio = AudioSegment.silent(duration=0)

        for i, row in enumerate(df.itertuples(index=False)):
            text = " ".join(str(x) for x in row if pd.notna(x))
            lang = detect_lang(text)
            tts = gTTS(text=text, lang=lang)
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            segment = AudioSegment.from_file(buf, format="mp3")
            temp_audio += segment + AudioSegment.silent(duration=int(pause_sec * 1000))

            progress = int((i + 1) / total_rows * 100)
            progress_bar.progress(progress)
            progress_text.text(f"Генерация {i+1}/{total_rows} строк...")

            # небольшая пауза, чтобы UI обновлялся
            time.sleep(0.05)

        temp_audio.export(mp3_combined, format="mp3")
        mp3_combined.seek(0)

        # Показать плеер и кнопку скачивания
        st.success("Генерация завершена!")
        st.audio(mp3_combined, format="audio/mp3")

        # Для кнопки скачивания используем отдельный буфер
        mp3_buf2 = BytesIO(mp3_combined.getvalue())
        st.download_button("💾 Скачать MP3", data=mp3_buf2, file_name="output.mp3")
