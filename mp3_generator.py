# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from gtts import gTTS
from pydub import AudioSegment

def _tts_to_segment(text: str, lang: str) -> AudioSegment:
    buf = BytesIO()
    tts = gTTS(text=text, lang=lang)
    tts.write_to_fp(buf)
    buf.seek(0)
    seg = AudioSegment.from_file(buf, format="mp3")
    return seg

def build_merged_mp3(rows, pause_ms: int = 500, ru_col: int = 0, ru_lang: str = "ru", de_lang: str = "de", progress_callback=None):
    track = AudioSegment.silent(duration=0)
    total = len(rows)
    first_ru_done = False

    for idx, row in enumerate(rows):
        cells = [str(c).strip() for c in row if c and str(c).strip().lower() not in ("nan", "none")]
        if not cells:
            if progress_callback:
                try: progress_callback(idx)
                except TypeError:
                    try: progress_callback(idx, total)
                    except Exception: pass
            continue

        # Русское слово с паузой
        if 0 <= ru_col < len(cells):
            if first_ru_done:
                track += AudioSegment.silent(duration=pause_ms)
            try:
                track += _tts_to_segment(cells[ru_col], ru_lang)
            except Exception as e:
                print(f"[WARN] gTTS RU failed for '{cells[ru_col]}': {e}")
            first_ru_done = True

        # Немецкие слова
        for j, text in enumerate(cells):
            if j == ru_col:
                continue
            try:
                track += _tts_to_segment(text, de_lang)
            except Exception as e:
                print(f"[WARN] gTTS DE failed for '{text}': {e}")

        if progress_callback:
            try: progress_callback(idx)
            except TypeError:
                try: progress_callback(idx, total)
                except Exception: pass

    out_buf = BytesIO()
    track.export(out_buf, format="mp3", bitrate="128k")
    out_buf.seek(0)
    return out_buf


def mp3_generator_block(user, df, pause_sec, selected_indices):
    if not selected_indices:
        st.info("Сначала выберите строки для генерации")
        return

    df_selected = df.loc[selected_indices].values.tolist()
    total = len(df_selected)

    st.subheader("🎧 Генератор MP3")
    if st.button("▶️ Сгенерировать MP3"):
        progress_bar = st.progress(0)
        def progress_callback(idx):
            progress_bar.progress((idx + 1) / total)

        # конвертируем паузу в миллисекунды
        pause_ms = int(pause_sec * 1000)
        mp3_buf = build_merged_mp3(df_selected, pause_ms=pause_ms, progress_callback=progress_callback)
        st.audio(mp3_buf, format="audio/mp3")
        st.download_button("💾 Скачать MP3", data=mp3_buf, file_name="output.mp3")
