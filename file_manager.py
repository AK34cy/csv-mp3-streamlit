# file_manager.py
import streamlit as st
import pandas as pd
from db import store_file, list_user_files, get_file

def file_manager_block(user):
    st.subheader("📂 Ваши файлы")

    uploaded = st.file_uploader("Загрузите CSV (без заголовков)", type="csv")
    if uploaded:
        df = pd.read_csv(uploaded, header=None).dropna(how="any").replace(r'^\s*$', pd.NA, regex=True).dropna(how="any").reset_index(drop=True)
        store_file(st.session_state.conn, user["id"], uploaded.name, uploaded.getvalue(), kind="csv")
        st.success(f"Файл '{uploaded.name}' сохранён в БД")
        st.experimental_rerun()

    # Список файлов из БД
    files = list_user_files(st.session_state.conn, user["id"], kind="csv")
    if files:
        for f in files:
            st.write(f"{f['filename']} ({f['created_at']})")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Открыть", key=f"open_{f['id']}"):
                    st.session_state.current_file_id = f['id']
                    st.experimental_rerun()
            with col2:
                if st.button("Удалить", key=f"del_{f['id']}"):
                    st.session_state.conn.cursor().execute("DELETE FROM user_files WHERE id=%s AND user_id=%s", (f['id'], user["id"]))
                    st.success(f"Файл '{f['filename']}' удалён")
                    st.experimental_rerun()
    else:
        st.info("Нет загруженных CSV")
