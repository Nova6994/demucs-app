# demucsapp.py

import streamlit as st
from utils import download_youtube_audio, run_demucs
import os
import shutil

st.set_page_config(page_title="🎧 Demucs Stem Separator", layout="wide")

st.title("🎶 Demucs Stem Separator")
st.markdown("""
Upload an audio file **or** enter a YouTube link to isolate stems using [Demucs](https://github.com/facebookresearch/demucs).
""")

model = st.selectbox("Select Demucs Model", ["htdemucs", "demucs"])
device = st.selectbox("Select Processing Device", ["cpu", "cuda (GPU)"])
input_mode = st.radio("Input Type", ["Upload Audio", "YouTube URL"])

audio_path = None
temp_files = []

if input_mode == "Upload Audio":
    uploaded = st.file_uploader("Upload your audio file:", type=["mp3", "wav", "flac", "ogg", "m4a"])
    if uploaded:
        path = f"temp_{uploaded.name}"
        with open(path, "wb") as f:
            f.write(uploaded.getbuffer())
        audio_path = path
        temp_files.append(path)

else:
    url = st.text_input("Enter YouTube URL:")
    if url:
        with st.spinner("Downloading audio..."):
            try:
                audio_path = download_youtube_audio(url)
                temp_files.append(audio_path)
                st.success("YouTube audio downloaded successfully!")
            except Exception as e:
                st.error(f"Error downloading audio: {e}")

if audio_path:
    if st.button("🎛️ Run Demucs Separation"):
        with st.spinner("Separating stems... please wait..."):
            try:
                out_dir = run_demucs(audio_path, model=model, device=device)
                st.success("Done! Choose your stems below:")

                stem_files = sorted(os.listdir(out_dir))
                for file in stem_files:
                    path = os.path.join(out_dir, file)
                    st.audio(path)
                    with open(path, "rb") as f:
                        st.download_button(f"Download {file}", data=f, file_name=file)

            except Exception as e:
                st.error(f"Error during Demucs separation: {e}")
