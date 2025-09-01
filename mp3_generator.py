# mp3_generator.py
import pandas as pd
from gtts import gTTS
from pydub import AudioSegment
from io import BytesIO
from db import get_file
import streamlit as st

def _tts_to_segment(text: str, lang: str) -> AudioSegment:
    buf = BytesIO()
    tts = gTTS(text=text, lang=lang)
    tts.write_to_fp(buf)
    buf.seek(0)
    seg = AudioSegment.from_file(buf, format="mp3")
    return seg

def mp3_generator_block(user):
    if "current_file_id" not in st.session_state:
        st.info("Сначала выберите файл в разделе 'Файлы'")
        return

    conn = st.session_state.conn
    file_data = get_file(conn, st.session_state.current_file_id, user["id"])
    if not file_data:
        st.error("Файл не найден")
        return

    st.subheader(f"🎧 Генерация MP3: {file_data['filename']}")
    pause_sec = st.slider("Пауза перед русским словом (сек)", 0.0, 5.0, 0.3, 0.1)

    df = pd.read_csv(BytesIO(file_data['data']), header=None).dropna(how="any").reset_index(drop=True)
    selected = st.multiselect("Выберите строки для генерации", df.index.tolist(), default=df.index.tolist())

    if st.button("Сгенерировать MP3"):
        track = AudioSegment.silent(duration=0)
        first_ru_done = False
        for idx in selected:
            row = df.loc[idx].astype(str).tolist()
            if 0 < len(row):
                if first_ru_done:
                    track += AudioSegment.silent(duration=int(pause_sec*1000))
                track += _tts_to_segment(row[0], "ru")
                first_ru_done = True
            for j, t in enumerate(row):
                if j == 0:
                    continue
                track += _tts_to_segment(t, "de")
        buf = BytesIO()
        track.export(buf, format="mp3", bitrate="128k")
        buf.seek(0)
        st.audio(buf.getvalue(), format="audio/mpeg")
        st.download_button("⬇️ Скачать MP3", buf.getvalue(), file_name=f"{file_data['filename'].rsplit('.',1)[0]}_mp3.mp3", mime="audio/mpeg")
