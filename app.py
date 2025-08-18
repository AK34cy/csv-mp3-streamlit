import streamlit as st
import pandas as pd
from gtts import gTTS
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

st.title("CSV Loader + MP3 Generator")

uploaded_file = st.file_uploader("Загрузите CSV файл", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gridOptions = gb.build()
    
    st.subheader("Таблица CSV")
    grid_response = AgGrid(
        df,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True
    )
    
    selected_rows = grid_response['selected_rows']
    
    if selected_rows:
        st.subheader("Выбранные строки")
        selected_df = pd.DataFrame(selected_rows)
        st.dataframe(selected_df)
        
        text = " ".join(selected_df.astype(str).agg(" ".join, axis=1))
        if st.button("Сгенерировать MP3"):
            tts = gTTS(text, lang='ru')
            mp3_fp = BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            
            st.audio(mp3_fp, format='audio/mp3')
            st.download_button(
                "Скачать MP3",
                data=mp3_fp,
                file_name="output.mp3",
                mime="audio/mp3"
            )
