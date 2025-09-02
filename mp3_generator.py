# mp3_generator.py
import streamlit as st
import pandas as pd
from io import BytesIO
from gtts import gTTS
from pydub import AudioSegment
from pydub.utils import which as pydub_which
import logging
import traceback
import os
from typing import Optional

logger = logging.getLogger(__name__)


def _ensure_ffmpeg():
    """Проверить ffmpeg и задать AudioSegment.converter, если найден."""
    ffmpeg_path = pydub_which("ffmpeg") or pydub_which("ffmpeg.exe")
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg не найден в PATH (нужен pydub для работы с mp3). Установите ffmpeg и перезапустите сервис.")
    # явно укажем pydub, чтобы он использовал конкретный бинарник
    AudioSegment.converter = ffmpeg_path
    return ffmpeg_path


def build_merged_mp3(df: pd.DataFrame, pause_sec: float = 0.5, debug_save_path: Optional[str] = None) -> bytes:
    """
    Генерация MP3 из DataFrame. Возвращает raw bytes MP3.
    pause_sec — пауза между строками (в секундах).
    debug_save_path — если указан, сохранить итоговый mp3 на диск для отладки.
    """
    if df is None or df.empty:
        raise ValueError("DataFrame пустой")

    # проверяем ffmpeg
    _ensure_ffmpeg()

    mp3_combined = AudioSegment.silent(duration=0)

    for row in df.itertuples(index=False):
        # конструируем текст из непустых ячеек строки
        text = " ".join(str(x) for x in row if pd.notna(x) and str(x).strip() != "")
        if not text.strip():
            continue
        try:
            tts = gTTS(text=text, lang="ru")
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            # pydub использует ffmpeg для чтения mp3 из буфера
            segment = AudioSegment.from_file(buf, format="mp3")
            mp3_combined += segment
            # пауза между строками
            if pause_sec and pause_sec > 0:
                mp3_combined += AudioSegment.silent(duration=int(pause_sec * 1000))
        except Exception as e:
            # логируем и пробрасываем, чтобы вызвавший блок показал ошибку
            logger.exception("gTTS/pydub error for text: %s", text)
            raise

    out_buf = BytesIO()
    mp3_combined.export(out_buf, format="mp3")
    mp3_bytes = out_buf.getvalue()

    # опционально сохраняем на диск (удобно для диагностики)
    if debug_save_path:
        try:
            with open(debug_save_path, "wb") as f:
                f.write(mp3_bytes)
            logger.info("Saved debug MP3 to %s", debug_save_path)
        except Exception:
            logger.exception("Failed to save debug mp3 to %s", debug_save_path)

    # простая проверка
    if not mp3_bytes or len(mp3_bytes) < 2000:
        # слишком маленький файл — скорее всего что-то пошло не так
        raise RuntimeError(f"Сгенерирован слишком маленький MP3 ({len(mp3_bytes)} bytes). Проверьте ffmpeg/gTTS.")

    return mp3_bytes


def mp3_generator_block(user: dict, df: pd.DataFrame, pause_sec: float, file_name: str = "output"):
    """
    Streamlit-блок генерации MP3 (вариант 2).
    Принимает user, df (DataFrame с выбранными строками), pause_sec и file_name (без .mp3).
    """
    st.subheader("🎧 Генератор MP3")

    if df is None or df.empty:
        st.info("Нет данных для генерации MP3")
        return

    # Защитим UI: отключаем кнопку при повторном нажатии
    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация..."):
            try:
                # debug_save_path можно временно задать для проверки (например "/tmp/out.mp3")
                debug_path = os.environ.get("MP3_DEBUG_SAVE")  # опционально: задайте в окружении
                mp3_bytes = build_merged_mp3(df, pause_sec=pause_sec, debug_save_path=debug_path)

                # отдаем байты плееру и кнопке скачивания
                st.audio(mp3_bytes, format="audio/mpeg")  # используем audio/mpeg
                st.download_button(
                    "💾 Скачать MP3",
                    data=mp3_bytes,
                    file_name=f"{file_name}.mp3",
                    mime="audio/mpeg"
                )
            except Exception as e:
                # показываем пользователю понятную ошибку и стек для диагностики
                st.error(f"Ошибка при генерации MP3: {e}")
                st.text_area("Подробный трейсбек (для диагностики):", traceback.format_exc(), height=300)
                logger.exception("mp3 generation failed")
