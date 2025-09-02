# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from gtts import gTTS
from pydub import AudioSegment

def build_merged_mp3(df, pause_sec=0.5):
    """
    Генерация MP3 из DataFrame.
    Каждая строка df превращается в звук, пауза между строками = pause_sec секунд.
    """
    mp3_combined = AudioSegment.silent(duration=0)

    for row in df.itertuples(index=False):
        text = " ".join(str(x) for x in row if pd.notna(x))
        if not text.strip():
            continue
        tts = gTTS(text=text, lang="ru")
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        segment = AudioSegment.from_file(buf, format="mp3")
        mp3_combined += segment + AudioSegment.silent(duration=int(pause_sec * 1000))

    out_buf = BytesIO()
    mp3_combined.export(out_buf, format="mp3")
    out_buf.seek(0)
    return out_buf

def mp3_generator_block(user, df, pause_sec):
    """
    Streamlit-блок генерации MP3.
    Получает готовый DataFrame и паузу между строками.
    """
    st.subheader("🎧 Генератор MP3")

    if df is None or df.empty:
        st.warning("Нет данных для генерации MP3")
        return

    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация..."):
            mp3_buf = build_merged_mp3(df, pause_sec=pause_sec)
            st.audio(mp3_buf, format="audio/mp3")
            st.download_button(
                "💾 Скачать MP3",
                data=mp3_buf,
                file_name="output.mp3"
            )
