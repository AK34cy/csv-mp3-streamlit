# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from db import get_file
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

def mp3_generator_block(user):
    """
    Streamlit-блок генерации MP3.
    Требуется, чтобы пользователь уже выбрал файл (st.session_state.current_file_id).
    """
    st.subheader("🎧 Генератор MP3")

    conn = st.session_state.conn

    if "current_file_id" not in st.session_state:
        st.info("Сначала выберите файл слева")
        return

    file_data = get_file(conn, st.session_state.current_file_id, user["id"])
    if not file_data:
        st.error("Файл не найден")
        return

    file_name = file_data['filename']

    # Чтение CSV
    df = pd.read_csv(BytesIO(file_data['data']), header=None).dropna(how="any").reset_index(drop=True)

    st.write(f"Выбран файл: **{file_name}** ({len(df)} строк)")

    # Параметр паузы
    pause_sec = st.slider(
        "Пауза между строками, сек",
        min_value=0.0, max_value=5.0, value=0.5, step=0.1
    )

    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация..."):
            mp3_buf = build_merged_mp3(df, pause_sec=pause_sec)
            st.audio(mp3_buf, format="audio/mp3")
            st.download_button(
                "💾 Скачать MP3",
                data=mp3_buf,
                file_name=f"{file_name}.mp3"
            )
