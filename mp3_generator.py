import streamlit as st
from gtts import gTTS
from pydub import AudioSegment
from io import BytesIO
from tempfile import NamedTemporaryFile
import pandas as pd

def _tts_to_segment(text: str, lang: str) -> AudioSegment:
    """Преобразует текст в аудиосегмент через gTTS"""
    buf = BytesIO()
    tts = gTTS(text=text, lang=lang)
    tts.write_to_fp(buf)
    buf.seek(0)
    return AudioSegment.from_file(buf, format="mp3")


def build_merged_mp3(rows, selected_indices, pause_ms: int = 500, ru_col: int = 0, ru_lang="ru", de_lang="de", progress_callback=None):
    """
    Генерация MP3 для выбранных строк.
    rows — DataFrame
    selected_indices — список индексов выбранных строк
    """
    track = AudioSegment.silent(duration=0)
    first_ru_done = False
    total = len(selected_indices)

    for idx, row_idx in enumerate(selected_indices):
        row = rows.iloc[row_idx]
        cells = [str(c).strip() for c in row if pd.notna(c) and str(c).strip().lower() not in ("nan", "none")]
        if not cells:
            if progress_callback:
                progress_callback(idx, total)
            continue

        # Русское слово
        if 0 <= ru_col < len(cells):
            if first_ru_done:
                track += AudioSegment.silent(duration=pause_ms)
            try:
                track += _tts_to_segment(cells[ru_col], ru_lang)
            except Exception as e:
                print(f"[WARN] gTTS RU failed for '{cells[ru_col]}': {e}")
            first_ru_done = True

        # Остальные слова (немецкие)
        for j, text in enumerate(cells):
            if j == ru_col:
                continue
            try:
                track += _tts_to_segment(text, de_lang)
            except Exception as e:
                print(f"[WARN] gTTS DE failed for '{text}': {e}")

        if progress_callback:
            progress_callback(idx + 1, total)

    # Сохраняем MP3 на диск
    tmp_file = NamedTemporaryFile(delete=False, suffix=".mp3")
    track.export(tmp_file.name, format="mp3", bitrate="128k")
    tmp_file.close()
    return tmp_file.name


def mp3_generator_block(user, df, pause_sec, selected_indices):
    """
    Streamlit-блок генерации MP3.
    """
    st.subheader("🎧 Генератор MP3")

    if not selected_indices:
        st.info("Сначала выберите строки слева")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация MP3..."):
            def progress_callback(current, total):
                progress_bar.progress(current / total)
                status_text.text(f"Генерация: {current}/{total} строк")

            tmp_path = build_merged_mp3(df, selected_indices, pause_ms=int(pause_sec * 1000), progress_callback=progress_callback)

            st.success("Генерация завершена!")
            st.audio(tmp_path, format="audio/mp3")

            with open(tmp_path, "rb") as f:
                st.download_button("💾 Скачать MP3", data=f, file_name="output.mp3")
