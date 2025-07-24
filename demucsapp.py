# demucsapp.py

import streamlit as st
import os
from utils import download_youtube_audio, run_demucs
import shutil
import zipfile
import base64
from pathlib import Path

st.set_page_config(page_title="Demucs Stem Splitter", page_icon="🎵", layout="centered")

st.markdown("""
    <style>
    body {
        background-color: #111;
        color: #fff;
    }
    .stApp {
        background-color: #111;
    }
    h1, h2, h3, h4, h5, h6, p, div {
        color: #fff;
    }
    .stButton>button {
        color: white;
        background-color: #d00000;
        border-radius: 8px;
        border: none;
        padding: 0.5em 1em;
        font-size: 1em;
    }
    .stTextInput>div>div>input {
        background-color: #222;
        color: white;
    }
    .stSelectbox>div>div>div {
        background-color: #222;
        color: white;
    }
    .stFileUploader>div>div>div>input[type=file] {
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎶 Demucs Stem Splitter")
st.write("Split audio into individual stems using Facebook's Demucs model. Works with YouTube links or uploaded audio files.")

option = st.radio("Choose your input method:", ("YouTube Link", "Upload File"))

model = st.selectbox("Select model:", ["htdemucs", "htdemucs_6s"])
device = st.selectbox("Device:", ["cpu"])  # GPU can be added if available

audio_path = None

if option == "YouTube Link":
    url = st.text_input("Enter YouTube URL:")
    if st.button("Download and Process") and url:
        try:
            st.info("Downloading audio from YouTube...")
            audio_path = download_youtube_audio(url)
        except Exception as e:
            st.error(f"Download failed: {e}")

elif option == "Upload File":
    uploaded_file = st.file_uploader("Upload an audio file:", type=["mp3", "wav", "m4a"])
    if uploaded_file:
        temp_dir = Path("temp_upload")
        temp_dir.mkdir(exist_ok=True)
        audio_path = str(temp_dir / uploaded_file.name)
        with open(audio_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

if audio_path:
    if st.button("Run Demucs Split"):
        try:
            st.info("Running Demucs...")
            separated_path = run_demucs(audio_path, model=model, device=device)

            # Zip results
            zip_path = shutil.make_archive("separated_output", "zip", separated_path)
            with open(zip_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:application/zip;base64,{b64}" download="demucs_stems.zip">⬇️ Download stems</a>'
                st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Demucs processing failed: {e}")

# Clean up
if Path("temp_upload").exists():
    shutil.rmtree("temp_upload", ignore_errors=True)
if Path("separated_output.zip").exists():
    os.remove("separated_output.zip")
