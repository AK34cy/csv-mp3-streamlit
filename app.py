import io
import pandas as pd
import streamlit as st
import bcrypt
from pydub.utils import which
from mp3_generator import build_merged_mp3

import db
from register import register_user

st.set_page_config(page_title="Списки слов → MP3", page_icon="🎧", layout="centered")
st.title("📚 Списки слов → общий MP3 (с аккаунтами)")

# --- БД (кэшируем соединение и создаём таблицы) ---
@st.cache_resource(show_spinner=False)
def _get_conn():
    conn = db.get_conn()
    db.init_db(conn)
    return conn

conn = _get_conn()

# --- Session state для auth ---
if "user" not in st.session_state:
    st.session_state.user = None

# --- Блок авторизации ---
def show_auth():
    tabs = st.tabs(["Вход", "Регистрация"])

    with tabs[0]:
        st.subheader("Вход")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Пароль", type="password", key="login_password")
        if st.button("Войти", type="primary"):
            u = db.get_user_by_email(conn, (email or "").strip().lower())
            if not u:
                st.error("Пользователь не найден")
            else:
                ok = bcrypt.checkpw((password or "").encode("utf-8"), u["password_hash"].encode("utf-8"))
                if ok:
                    st.session_state.user = {"id": u["id"], "email": u["email"], "name": u.get("name")}
                    st.success("Вход выполнен")
                    st.experimental_rerun()
                else:
                    st.error("Неверный пароль")

    with tabs[1]:
        st.subheader("Регистрация")
        r_email = st.text_input("Email", key="reg_email")
        r_name = st.text_input("Имя (необязательно)", key="reg_name")
        r_pwd = st.text_input("Пароль", type="password", key="reg_pwd")
        r_pwd2 = st.text_input("Повторите пароль", type="password", key="reg_pwd2")
        if st.button("Зарегистрироваться"):
            ok, msg, user = register_user(conn, r_email, r_name, r_pwd, r_pwd2)
            if ok:
                st.success(msg)
                st.info("Теперь выполните вход на вкладке «Вход».")
            else:
                st.error(msg)

if not st.session_state.user:
    show_auth()
    st.stop()

# --- Sidebar: профиль, выход, файлы из БД ---
with st.sidebar:
    st.markdown(f"**Профиль:** {st.session_state.user['email']}")
    if st.button("Выйти"):
        st.session_state.clear()
        st.experimental_rerun()

    st.markdown("—")
    st.subheader("Мои файлы (БД)")
    db_files = db.list_user_files(conn, st.session_state.user["id"], kind="csv")
    if db_files:
        options = {f"{r['filename']} • {r['created_at']:%Y-%m-%d %H:%M}": r["id"] for r in db_files}
        sel = st.selectbox("Загруженные CSV", list(options.keys()))
        colA, colB = st.columns(2)
        with colA:
            if st.button("Добавить в сессию"):
                rec = db.get_file(conn, options[sel], st.session_state.user["id"])
                if rec and rec["kind"] == "csv":
                    buf = io.BytesIO(rec["data"])
                    df = (
                        pd.read_csv(buf, header=None)
                        .dropna(how="any")
                        .replace(r'^\s*$', pd.NA, regex=True)
                        .dropna(how="any")
                        .reset_index(drop=True)
                    )
                    st.session_state.setdefault("uploaded_files", {})
                    st.session_state.setdefault("selected_rows", {})
                    st.session_state.setdefault("current_file", None)
                    # уникализируем имя
                    base = rec["filename"]
                    name = base
                    i = 1
                    while name in st.session_state["uploaded_files"]:
                        name = f"{base} ({i})"
                        i += 1
                    st.session_state["uploaded_files"][name] = df
                    st.session_state["selected_rows"].setdefault(name, [])
                    st.session_state["current_file"] = name
                    st.success(f"Файл '{name}' добавлен в сессию")
        with colB:
            if st.button("Скачать"):
                rec = db.get_file(conn, options[sel], st.session_state.user["id"])
                if rec:
                    st.download_button(
                        "Скачать выбранный CSV",
                        data=rec["data"],
                        file_name=rec["filename"],
                        mime="text/csv",
                    )

# --- Инициализация session state для интерфейса ---
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}
if "selected_rows" not in st.session_state:
    st.session_state.selected_rows = {}
if "current_file" not in st.session_state:
    st.session_state.current_file = None

# --- Загрузка CSV (и сохранение в БД) ---
uploaded = st.file_uploader("Загрузите CSV-файл (без заголовков)", type="csv")
if uploaded is not None:
    # 1) Сохраняем ОРИГИНАЛ в БД
    try:
        db.store_file(conn, st.session_state.user["id"], uploaded.name, uploaded.getvalue(), kind="csv")
        st.success("CSV сохранён в БД")
    except Exception as e:
        st.warning(f"Не удалось сохранить в БД: {e}")

    # 2) Готовим DataFrame для сессии (очистка)
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
    st.success(f"Файл '{uploaded.name}' загружен в сессию")

# --- Выбор файла и работа с ним ---
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

    st.subheader("📂 Загруженные файлы (сессия):")
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

    # --- параметры генерации (пауза ПЕРЕД русским, кроме первого) ---
    st.subheader("⚙️ Параметры озвучки")
    pause_sec = st.slider("Пауза перед русским словом (кроме первого), сек", 0.0, 5.0, 0.5, 0.1)

    # --- генерация MP3 ---
    st.subheader("🎧 Генерация")
    if st.button("Сгенерировать общий MP3"):
        if not new_selected:
            st.warning("Сначала выберите хотя бы одну строку.")
        else:
            if which("ffmpeg") is None and which("ffmpeg.exe") is None:
                st.error("ffmpeg не найден в контейнере")
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

                    # по желанию можно сохранять MP3 в БД:
                    # db.store_file(conn, st.session_state.user["id"], f"{file_name}_selected.mp3", mp3_bytes, kind="mp3")

                    st.caption(f"Размер файла: {len(mp3_bytes)/1024:.1f} KB")

                except Exception as e:
                    progress_bar.empty()
                    status.empty()
                    st.error(f"Ошибка при генерации: {e}")

# --- удаление файлов из сессии ---
if st.session_state.uploaded_files:
    st.divider()
    file_to_delete = st.selectbox("Удалить из сессии", list(st.session_state.uploaded_files.keys()))
    if st.button("Удалить файл из сессии"):
        st.session_state.uploaded_files.pop(file_to_delete, None)
        st.session_state.selected_rows.pop(file_to_delete, None)
        if st.session_state.current_file == file_to_delete:
            st.session_state.current_file = next(iter(st.session_state.uploaded_files), None)
        st.success(f"Файл '{file_to_delete}' удалён из сессии")
