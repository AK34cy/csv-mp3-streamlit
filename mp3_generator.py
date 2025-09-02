# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from db import get_file
from gtts import gTTS
from pydub import AudioSegment
from pydub.utils import which

# Явно указываем путь к ffmpeg, чтобы избежать проблем с конвертацией
AudioSegment.converter = which("ffmpeg")


def build_merged_mp3(df: pd.DataFrame, pause_sec: float = 0.5) -> bytes:
    """
    Генерация MP3 из DataFrame.
    Каждая строка df превращается в звук, пауза между строками = pause_sec секунд.
    Возвращает готовый байтовый поток для Streamlit.
    """
    mp3_combined = AudioSegment.silent(duration=0)

    for row in df.itertuples(index=False):
        text = " ".join(str(x) for x in row if pd.notna(x))
        tts = gTTS(text=text, lang="ru")
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        segment = AudioSegment.from_file(buf, format="mp3")
        mp3_combined += segment + AudioSegment.silent(duration=int(pause_sec * 1000))

    out_buf = BytesIO()
    mp3_combined.export(out_buf, format="mp3")
    return out_buf.getvalue()  # Возвращаем именно bytes для Streamlit


def mp3_generator_block(user, df: pd.DataFrame, pause_sec: float = 0.5):
    """
    Streamlit-блок генерации MP3.
    Требуется, чтобы пользователь уже выбрал файл и передан DataFrame df.
    """
    st.subheader("🎧 Генератор MP3")

    st.write(f"Выбран файл: **{st.session_state.get('current_file_name', '—')}** ({len(df)} строк)")

    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация..."):
            mp3_bytes = build_merged_mp3(df, pause_sec=pause_sec)
            st.audio(mp3_bytes, format="audio/mpeg")
            st.download_button(
                "💾 Скачать MP3",
                data=mp3_bytes,
                file_name=f"{st.session_state.get('current_file_name', 'output')}.mp3"
            )
