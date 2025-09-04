# word_list_ui.py
import streamlit as st
import pandas as pd


def render_word_list(file_name, df):
    """Блок работы со списком слов и выбор параметров генерации"""

    if "selected_rows" not in st.session_state:
        st.session_state.selected_rows = {}

    top_key = f"select_all_top_{file_name}"
    bottom_key = f"select_all_bottom_{file_name}"

    def _sync_select_all(file_name_arg, which):
        """Синхронизация чекбоксов 'выбрать все' сверху и снизу"""
        top_k = f"select_all_top_{file_name_arg}"
        bot_k = f"select_all_bottom_{file_name_arg}"
        val = st.session_state.get(top_k) if which == "top" else st.session_state.get(bot_k)

        st.session_state[top_k] = val
        st.session_state[bot_k] = val

        for i in df.index:
            st.session_state[f"{file_name_arg}_{i}"] = val

    # Инициализация состояния "выбрать все"
    if top_key not in st.session_state:
        st.session_state[top_key] = False
    if bottom_key not in st.session_state:
        st.session_state[bottom_key] = False

    # Инициализация состояния по строкам
    for i in df.index:
        k = f"{file_name}_{i}"
        if k not in st.session_state:
            st.session_state[k] = False

    # Верхний чекбокс "выбрать все"
    st.checkbox("**✅ ВЫБРАТЬ / СНЯТЬ ВСЕ**", key=top_key,
                on_change=_sync_select_all, args=(file_name, "top"))

    # Список строк
    selected_indices = []
    for i, row in df.iterrows():
        row_text = " | ".join(str(x) for x in row if pd.notna(x))
        if st.checkbox(row_text, key=f"{file_name}_{i}"):
            selected_indices.append(i)

    # Нижний чекбокс "выбрать все"
    st.checkbox("**✅ ВЫБРАТЬ / СНЯТЬ ВСЕ**", key=bottom_key,
                on_change=_sync_select_all, args=(file_name, "bottom"))

    # Сохраняем выбор в session_state
    st.session_state.selected_rows[file_name] = selected_indices

    st.write(f"Выбрано: {len(selected_indices)} строк")

    # --- Параметры генерации ---
    st.subheader("⚙️ Параметры озвучки")
    pause_sec = st.slider(
        "Пауза перед русским словом (кроме первого), сек",
        0.0, 5.0, 0.5, 0.1
    )

    return pause_sec, selected_indices
