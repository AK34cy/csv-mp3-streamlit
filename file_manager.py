import streamlit as st
from db import list_user_files, store_file, get_file
from db import get_conn
import os


def file_manager_block(user):
    st.header("Файлы")

    uploaded = st.file_uploader("Загрузите CSV файл", type=["csv"])
    if uploaded:
        data = uploaded.read()
        file_id = store_file(st.session_state.conn, user["id"], uploaded.name, data, kind="csv")
        st.success(f"Файл сохранён (ID {file_id})")
        st.rerun()

    files = list_user_files(st.session_state.conn, user["id"], kind="csv")
    if not files:
        st.info("Файлы ещё не загружены")
        return

    st.subheader("Ваши файлы")
    for f in files:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"{f['filename']} ({f['created_at']})")
        with col2:
            if st.button("Удалить", key=f"del_{f['id']}"):
                with st.session_state.conn.cursor() as cur:
                    cur.execute("DELETE FROM user_files WHERE id=%s AND user_id=%s", (f["id"], user["id"]))
                st.success("Файл удалён")
                st.rerun()
