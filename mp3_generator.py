# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from gtts import gTTS
from pydub import AudioSegment

def build_merged_mp3(df, pause_sec=0.5):
    """
    Генерация MP3 из DataFrame.
    Каждая строка df превращается в речь, пауза между строками = pause_sec секунд.
    Возвращает байты MP3.
    """
    mp3_combined = AudioSegment.silent(duration=0)

    for row in df.itertuples(index=False):
        text = " ".join(str(x) for x in row if pd.notna(x))
        if not text.strip():
            continue
        # Генерация речи
        tts = gTTS(text=text, lang="ru")
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        segment = AudioSegment.from_file(buf, format="mp3")
        mp3_combined += segment + AudioSegment.silent(duration=int(pause_sec * 1000))

    # Экспорт в память
    out_buf = BytesIO()
    mp3_combined.export(out_buf, format="mp3")
    return out_buf.getvalue()


def mp3_generator_block(user, df, pause_sec=0.5, file_name="output"):
    """
    Streamlit-блок генерации MP3.
    Принимает:
      - user: dict с данными пользователя
      - df: DataFrame с контентом
      - pause_sec: пауза между строками
      - file_name: имя файла (без расширения)
    """
    st.subheader("🎧 Генератор MP3")

    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация..."):
            mp3_bytes = build_merged_mp3(df, pause_sec=pause_sec)
            st.audio(mp3_bytes, format="audio/mp3")
            st.download_button(
                "💾 Скачать MP3",
                data=mp3_bytes,
                file_name=f"{file_name}.mp3",
                mime="audio/mp3"
            )
