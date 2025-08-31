"""
mp3_generator.py
Модуль для генерации MP3-файлов из списка слов с помощью gTTS + pydub.
"""

from gtts import gTTS
from pydub import AudioSegment
from io import BytesIO


def _tts_to_segment(text: str, lang: str) -> AudioSegment:
    """Генерация фрагмента аудио из текста (gTTS → AudioSegment)."""
    buf = BytesIO()
    tts = gTTS(text=text, lang=lang)
    tts.write_to_fp(buf)
    buf.seek(0)
    return AudioSegment.from_file(buf, format="mp3")


def build_merged_mp3(
    rows,
    pause_ms: int = 500,   # пауза перед русским словом
    ru_col: int = 0,
    ru_lang: str = "ru",
    de_lang: str = "de",
    progress_callback=None,
):
    """
    Создаёт единый MP3-файл из списка слов.
    rows: список строк (list[list[str]])
    pause_ms: пауза перед русским словом
    ru_col: индекс колонки с русским словом
    ru_lang: язык для русских слов
    de_lang: язык для иностранных слов
    progress_callback: функция прогресса (idx, total)
    """
    track = AudioSegment.silent(duration=0)
    total = len(rows)
    first_ru_done = False

    for idx, row in enumerate(rows):
        cells = [
            str(c).strip()
            for c in row
            if c and str(c).strip().lower() not in ("nan", "none")
        ]
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

        # Остальные слова (например, немецкие)
        for j, text in enumerate(cells):
            if j == ru_col:
                continue
            try:
                track += _tts_to_segment(text, de_lang)
            except Exception as e:
                print(f"[WARN] gTTS DE failed for '{text}': {e}")

        if progress_callback:
            progress_callback(idx, total)

    out_buf = BytesIO()
    track.export(out_buf, format="mp3", bitrate="128k")
    out_buf.seek(0)
    return out_buf
