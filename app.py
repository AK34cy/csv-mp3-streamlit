import streamlit as st
import pandas as pd
from mp3_generator import build_merged_mp3
from pydub.utils import which

st.title("📚 Списки слов → общий MP3 (множественные файлы)")

# --- session state ---
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}
if "selected_rows" not in st.session_state:
    st.session_state.selected_rows = {}
if "current_file" not in st.session_state:
    st.session_state.current_file = None

# --- загрузка файлов ---
uploaded = st.file_uploader("Загрузите CSV-файл (без заголовков)", type="csv")
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
    st.session_state.current_file = uploaded.name
    st.success(f"Файл '{uploaded.name}' загружен")

# --- выбор файла для работы ---
if st.session_state.uploaded_files:
    st.markdown('<p style="font-size:20px;"><b>Выберите файл для работы:</b></p>', unsafe_allow_html=True)
    file_name = st.selectbox(
        "",
        list(st.session_state.uploaded_files.keys()),
        index=list(st.session_state.uploaded_files.keys()).index(
            st.session_state.current_file
        ) if st.session_state.current_file else 0
    )
    st.session_state.current_file = file_name
    df = st.session_state.uploaded_files[file_name]

    st.subheader("📂 Загруженные файлы:")
    for fname in st.session_state.uploaded_files.keys():
        if fname == file_name:
            st.markdown(f"<span style='background-color:#a0e0ff;padding:2px 6px;'>{fname}</span>", unsafe_allow_html=True)
        else:
            st.markdown(fname)

    # --- выбор строк ---
    st.subheader(f"✅ Выбор строк из '{file_name}'")
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

    if top_key not in st.session_state:
        st.session_state[top_key] = False
    if bottom_key not in st.session_state:
        st.session_state[bottom_key] = False
    for i in df.index:
        k = f"{file_name}_{i}"
        if k not in st.session_state:
            st.session_state[k] = False

    st.checkbox("**✅ ВЫБРАТЬ / СНЯТЬ ВСЕ**", key=top_key, on_change=_sync_select_all, args=(file_name, "top"))

    new_selected = []
    for i, row in df.iterrows():
        row_text = " | ".join(str(x) for x in row if pd.notna(x))
        if st.checkbox(row_text, key=f"{file_name}_{i}"):
            new_selected.append(i)

    st.checkbox("**✅ ВЫБРАТЬ / СНЯТЬ ВСЕ**", key=bottom_key, on_change=_sync_select_all, args=(file_name, "bottom"))

    st.session_state.selected_rows[file_name] = new_selected
    st.write(f"Выбрано: {len(new_selected)} строк")

    # --- параметры генерации ---
    st.subheader("⚙️ Параметры озвучки")
    pause_sec = st.slider("Пауза перед русским словом (кроме первого), сек", 0.0, 5.0, 0.5, 0.1)

    # --- генерация MP3 ---
    st.subheader("🎧 Генерация")
    if st.button("Сгенерировать общий MP3"):
        if not new_selected:
            st.warning("Сначала выбери хотя бы одну строку.")
        else:
            if which("ffmpeg") is None and which("ffmpeg.exe") is None:
                st.error("ffmpeg не найден. Установи ffmpeg и перезапусти приложение.")
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

# --- удаление файлов ---
if st.session_state.uploaded_files:
    st.divider()
    file_to_delete = st.selectbox("Выберите файл для удаления", list(st.session_state.uploaded_files.keys()))
    if st.button("Удалить файл"):
        st.session_state.uploaded_files.pop(file_to_delete, None)
        st.session_state.selected_rows.pop(file_to_delete, None)
        if st.session_state.current_file == file_to_delete:
            st.session_state.current_file = next(iter(st.session_state.uploaded_files), None)
        st.success(f"Файл '{file_to_delete}' удалён")