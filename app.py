import streamlit as st
import pandas as pd
from mp3_generator import build_merged_mp3
from pydub.utils import which
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

st.set_page_config(page_title="Списки слов → MP3", layout="wide")
st.title("📚 Списки слов → общий MP3")

# --- Подключение к БД ---
# Локально: загружаем .env
load_dotenv()
DB_URL = os.getenv("POSTGRES_URL") or st.secrets.get("POSTGRES_URL")

if not DB_URL:
    st.error("Не найден параметр подключения к БД. Установите POSTGRES_URL в .env или st.secrets")
    st.stop()

engine = create_engine(DB_URL)

# --- session state ---
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}  # имя файла -> DataFrame
if "selected_rows" not in st.session_state:
    st.session_state.selected_rows = {}  # имя файла -> список индексов
if "current_file" not in st.session_state:
    st.session_state.current_file = None

# --- Sidebar: управление файлами ---
st.sidebar.header("📂 Управление файлами")

# загрузка нового файла
uploaded = st.sidebar.file_uploader("Загрузите CSV (без заголовков)", type="csv")
if uploaded is not None:
    df = (
        pd.read_csv(uploaded, header=None)
        .dropna(how="any")
        .replace(r'^\s*$', pd.NA, regex=True)
        .dropna(how="any")
        .reset_index(drop=True)
    )
    st.session_state.uploaded_files[uploaded.name] = df
    st.session_state.selected_rows.setdefault(uploaded.name, [])
    st.success(f"Файл '{uploaded.name}' загружен")

# список файлов
if st.session_state.uploaded_files:
    st.sidebar.subheader("Ваши файлы")
    # ---- Оборачиваем ключи в list(), чтобы можно было удалять ----
    for fname in list(st.session_state.uploaded_files.keys()):
        st.sidebar.text(fname)
        open_key = f"open_{fname}"
        del_key = f"del_{fname}"

        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Открыть", key=open_key):
                st.session_state.current_file = fname
        with col2:
            if st.button("Удалить", key=del_key):
                st.session_state.uploaded_files.pop(fname, None)
                st.session_state.selected_rows.pop(fname, None)
                if st.session_state.current_file == fname:
                    st.session_state.current_file = next(iter(st.session_state.uploaded_files), None)
                st.success(f"Файл '{fname}' удалён")
        st.sidebar.markdown("---")

# --- основной рабочий экран ---
if st.session_state.current_file:
    file_name = st.session_state.current_file
    df = st.session_state.uploaded_files[file_name]

    st.subheader(f"✅ Работа с файлом '{file_name}'")

    # --- выбор строк ---
    top_key = f"select_all_top_{file_name}"
    bottom_key = f"select_all_bottom_{file_name}"

    def _sync_select_all(file_name_arg, which):
        top_k = f"select_all_top_{file_name_arg}"
        bot_k = f"select_all_bottom_{file_name_arg}"
        val = st.session_state.get(top_k) if which == "top" else st.session_state.get(bot_k)
        st.session_state[top_k] = val
        st.session_state[bot_k] = val
        for i in df.index:
            st.session_state[f"{file_name_arg}_{i}"] = val

    # инициализация ключей
    if top_key not in st.session_state:
        st.session_state[top_key] = False
    if bottom_key not in st.session_state:
        st.session_state[bottom_key] = False
    for i in df.index:
        k = f"{file_name}_{i}"
        if k not in st.session_state:
            st.session_state[k] = False

    # верхний чекбокс
    st.checkbox("**✅ ВЫБРАТЬ / СНЯТЬ ВСЕ**", key=top_key, on_change=_sync_select_all, args=(file_name, "top"))

    new_selected = []
    for i, row in df.iterrows():
        row_text = " | ".join(str(x) for x in row if pd.notna(x))
        if st.checkbox(row_text, key=f"{file_name}_{i}"):
            new_selected.append(i)

    # нижний чекбокс
    st.checkbox("**✅ ВЫБРАТЬ / СНЯТЬ ВСЕ**", key=bottom_key, on_change=_sync_select_all, args=(file_name, "bottom"))

    st.session_state.selected_rows[file_name] = new_selected
    st.write(f"Выбрано: {len(new_selected)} строк")

    # --- параметры генерации ---
    st.subheader("⚙️ Параметры озвучки")
    pause_sec = st.slider("Пауза перед русским словом (сек)", 0.0, 5.0, 0.3, 0.1)

    # --- генерация MP3 ---
    st.subheader("🎧 Генерация")
    if st.button("Сгенерировать общий MP3"):
        if not new_selected:
            st.warning("Сначала выберите хотя бы одну строку.")
        else:
            if which("ffmpeg") is None and which("ffmpeg.exe") is None:
                st.error("ffmpeg не найден. Установите ffmpeg и перезапустите приложение.")
            else:
                rows = df.loc[new_selected].astype(str).values.tolist()
                total = len(rows)
                progress_bar = st.progress(0)
                status = st.empty()

                def _cb(i):
                    pct = int((i + 1) / total * 100)
                    progress_bar.progress(pct)
                    status.text(f"🔊 Генерация... {i+1}/{total}")

                try:
                    with st.spinner("Синтез речи и склейка..."):
                        mp3_buf = build_merged_mp3(
                            rows=rows,
                            pause_ms=int(pause_sec * 1000),
                            ru_col=0,
                            ru_lang="ru",
                            de_lang="de",
                            progress_callback=_cb,
                        )

                    progress_bar.progress(100)
                    status.text("✅ Готово!")
                    st.success("Готово!")
                    mp3_buf.seek(0)
                    mp3_bytes = mp3_buf.getvalue()

                    st.audio(mp3_bytes, format="audio/mpeg")
                    st.download_button(
                        "⬇️ Скачать общий MP3",
                        data=mp3_bytes,
                        file_name=f"{file_name.rsplit('.',1)[0]}_selected.mp3",
                        mime="audio/mpeg",
                    )
                    st.caption(f"Размер файла: {len(mp3_bytes)/1024:.1f} KB")

                except Exception as e:
                    progress_bar.empty()
                    status.empty()
                    st.error(f"Ошибка при генерации: {e}")
