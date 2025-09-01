# file_manager.py
import streamlit as st
import pandas as pd
from db import store_file, list_user_files, get_file

def file_manager_block(user):
    st.subheader("📂 Ваши файлы")

    # --- Очистка зависших ключей session_state от предыдущих файлов ---
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith("file_") or k.startswith("current_file_")]
    for k in keys_to_clear:
        del st.session_state[k]

    uploaded = st.file_uploader("Загрузите CSV (без заголовков)", type="csv")
    if uploaded:
        try:
            df = (
                pd.read_csv(uploaded, header=None)
                .dropna(how="any")
                .replace(r'^\s*$', pd.NA, regex=True)
                .dropna(how="any")
                .reset_index(drop=True)
            )
            store_file(st.session_state.conn, user["id"], uploaded.name, uploaded.getvalue(), kind="csv")
            st.success(f"Файл '{uploaded.name}' сохранён в БД")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Ошибка при обработке файла: {e}")

    # Список файлов из БД
    files = list_user_files(st.session_state.conn, user["id"], kind="csv")
    if files:
        for f in files:
            st.write(f"{f['filename']} ({f['created_at']})")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Открыть", key=f"open_{f['id']}"):
                    file_data = get_file(st.session_state.conn, f['id'], user["id"])
                    if file_data and file_data.get("data"):
                        st.session_state.current_file_data = file_data
                        st.experimental_rerun()
                    else:
                        st.warning(f"Файл '{f['filename']}' недоступен или пустой")
            with col2:
                if st.button("Удалить", key=f"del_{f['id']}"):
                    try:
                        st.session_state.conn.cursor().execute(
                            "DELETE FROM user_files WHERE id=%s AND user_id=%s",
                            (f['id'], user["id"])
                        )
                        st.success(f"Файл '{f['filename']}' удалён")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Ошибка при удалении: {e}")
    else:
        st.info("Нет загруженных CSV")
