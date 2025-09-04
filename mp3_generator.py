import streamlit as st
from gtts import gTTS
from pydub import AudioSegment
from io import BytesIO
from tempfile import NamedTemporaryFile
import pandas as pd

def _tts_to_segment(text: str, lang: str) -> AudioSegment:
    """Преобразование текста в сегмент AudioSegment через gTTS"""
    buf = BytesIO()
    tts = gTTS(text=text, lang=lang)
    tts.write_to_fp(buf)
    buf.seek(0)
    return AudioSegment.from_file(buf, format="mp3")


def build_merged_mp3(
    rows,
    pause_ms: int = 500,
    ru_col: int = 0,
    ru_lang: str = "ru",
    de_lang: str = "de",
    progress_callback=None
):
    """
    Генерация MP3 из выбранных строк.
    rows — список списков (строки файла)
    pause_ms — пауза перед русским словом (кроме первого)
    """
    track = AudioSegment.silent(duration=0)
    total = len(rows)
    first_ru_done = False

    for idx, row in enumerate(rows):
        # Приведение к строкам и фильтр пустых
        cells = [str(c).strip() for c in row if c and str(c).strip().lower() not in ("nan", "none")]
        if not cells:
            if progress_callback:
                progress_callback(idx)
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
            progress_callback(idx + 1)

    # Сохраняем в BytesIO для передачи в Streamlit
    out_buf = BytesIO()
    track.export(out_buf, format="mp3", bitrate="128k")
    out_buf.seek(0)
    return out_buf


def mp3_generator_block(user, rows, pause_ms=500):
    """
    Streamlit-блок генерации MP3.
    rows — список выбранных строк из таблицы.
    """
    st.subheader("🎧 Генератор MP3")

    if not rows:
        st.info("Сначала выберите строки слева")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    def progress_callback(idx):
        progress = int((idx / len(rows)) * 100)
        progress_bar.progress(progress)
        status_text.text(f"Обработано {idx}/{len(rows)} строк")

    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация MP3..."):
            mp3_buf = build_merged_mp3(rows, pause_ms=int(pause_ms * 1000), progress_callback=progress_callback)
            progress_bar.progress(100)
            status_text.text(f"Готово! Всего {len(rows)} строк")

            # Сохраняем во временный файл для корректного воспроизведения
            with NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(mp3_buf.read())
                tmp_path = tmp.name

            st.audio(tmp_path, format="audio/mp3")

            with open(tmp_path, "rb") as f:
                st.download_button("💾 Скачать MP3", data=f, file_name="output.mp3")
