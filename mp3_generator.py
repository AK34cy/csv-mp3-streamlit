# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from gtts import gTTS
from pydub import AudioSegment

def build_merged_mp3(df: pd.DataFrame, selected_indices: list[int], pause_sec: float = 0.5):
    """
    Генерация MP3 из выбранных строк DataFrame.
    Каждая строка df превращается в звук, пауза между строками = pause_sec секунд.
    """
    mp3_combined = AudioSegment.silent(duration=0)
    selected_rows = df.iloc[selected_indices]

    progress_total = len(selected_rows)
    progress_bar = st.progress(0)

    for i, row in enumerate(selected_rows.itertuples(index=False), 1):
        text_parts = []
        for word in row:
            if pd.isna(word):
                continue
            # Простейшее определение языка
            lang = 'de' if any(ord(c) > 127 for c in str(word)) else 'ru'
            tts = gTTS(text=str(word), lang=lang)
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            segment = AudioSegment.from_file(buf, format="mp3")
            text_parts.append(segment)
        # Объединяем слова строки
        line_segment = sum(text_parts, AudioSegment.silent(duration=0))
        mp3_combined += line_segment + AudioSegment.silent(duration=int(pause_sec * 1000))
        progress_bar.progress(i / progress_total)

    out_buf = BytesIO()
    mp3_combined.export(out_buf, format="mp3")
    out_buf.seek(0)
    return out_buf

def mp3_generator_block(user, df: pd.DataFrame, pause_sec: float, selected_indices: list[int]):
    """
    Streamlit-блок генерации MP3.
    Требуется выбранный файл и список выбранных индексов строк.
    """
    st.subheader("🎧 Генератор MP3")
    if not selected_indices:
        st.info("Сначала выберите строки для генерации")
        return

    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация MP3..."):
            mp3_buf = build_merged_mp3(df, selected_indices, pause_sec=pause_sec)
            # Чтобы st.audio корректно воспроизводил буфер
            mp3_buf.seek(0)
            st.audio(mp3_buf.read(), format="audio/mp3")
            # Скачивание
            mp3_buf.seek(0)
            st.download_button("💾 Скачать MP3", data=mp3_buf.read(), file_name="output.mp3")
