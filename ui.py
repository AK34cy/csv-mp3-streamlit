import streamlit as st
from file_manager import upload_file, list_files, delete_file
from mp3_generator import build_merged_mp3


def render_file_upload(conn, user_id):
    """Блок загрузки файла"""
    st.subheader("📂 Загрузка файла")
    uploaded = st.file_uploader("Выберите CSV/Excel", type=["csv", "xlsx", "xls"])
    if uploaded:
        ok, msg = upload_file(conn, user_id, uploaded)
        if ok:
            st.success(msg)
        else:
            st.error(msg)


def render_file_list(conn, user_id):
    """Блок списка файлов"""
    st.subheader("📑 Мои файлы")
    files = list_files(conn, user_id)
    if not files:
        st.info("Файлы ещё не загружены")
        return None

    selected = st.radio("Выберите файл:", [f["name"] for f in files])
    file_map = {f["name"]: f for f in files}

    if st.button("🗑 Удалить выбранный файл"):
        ok, msg = delete_file(conn, file_map[selected]["id"])
        if ok:
            st.success(msg)
            st.experimental_rerun()
        else:
            st.error(msg)

    return file_map[selected]


def render_mp3_generator(rows):
    """Блок генерации MP3"""
    st.subheader("🎧 Генерация MP3")
    if not rows:
        st.info("Сначала загрузите и выберите файл")
        return

    if st.button("▶️ Сгенерировать MP3"):
        with st.spinner("Генерация..."):
            mp3_buf = build_merged_mp3(rows)
            st.audio(mp3_buf, format="audio/mp3")
            st.download_button("💾 Скачать MP3", data=mp3_buf, file_name="output.mp3")
