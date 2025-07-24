# dmucsapp.py

import streamlit as st
from pathlib import Path
import tempfile
import os
import shutil
from utils import download_youtube_audio, run_demucs, FFMPEG_BIN, FFPROBE_BIN
import torch

# Set page config and dark theme with red accent
st.set_page_config(page_title="Demucs Stem Separator", layout="centered")

# Custom CSS for black/red theme
st.markdown(
    """
    <style>
    body {
        background-color: #121212;
        color: #ff4444;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    }
    .css-18e3th9 {
        background-color: #121212;
    }
    .stButton>button {
        background-color: #ff4444;
        color: black;
        border-radius: 8px;
        font-weight: bold;
    }
    .stTextInput>div>input {
        background-color: #222222;
        color: #ff4444;
        border: 1px solid #ff4444;
        border-radius: 6px;
    }
    .stRadio>div>div>label {
        color: #ff4444;
        font-weight: bold;
    }
    .stFileUploader>div>input {
        color: #ff4444;
    }
    .stDownloadButton>button {
        background-color: #ff4444;
        color: black;
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎵 Demucs Stem Separator")

# Device selection
device = "cuda" if torch.cuda.is_available() else "cpu"
device = st.sidebar.selectbox("Select device", options=["cpu", "cuda"] if torch.cuda.is_available() else ["cpu"])

# Input selection
input_type = st.radio("Choose input type:", ["YouTube URL", "Upload Audio File"])

audio_file_path = None
temp_files = []

if input_type == "YouTube URL":
    url = st.text_input("Enter YouTube video URL:")
    if url:
        with st.spinner("Downloading audio from YouTube..."):
            try:
                audio_file_path = download_youtube_audio(url)
                temp_files.append(audio_file_path)
                st.success("Audio downloaded!")
            except Exception as e:
                st.error(f"Error downloading audio: {e}")
else:
    uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a", "flac", "ogg", "aac"])
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
            tmp.write(uploaded_file.read())
            audio_file_path = tmp.name
            temp_files.append(audio_file_path)
        st.success(f"Uploaded file: {uploaded_file.name}")

if audio_file_path:
    st.write(f"Ready to separate audio file: {Path(audio_file_path).name}")

    # Model selection
    model = st.selectbox("Select Demucs model:", options=["htdemucs", "demucs", "tasnet"])

    if st.button("Separate Audio"):
        with st.spinner("Separating stems... This may take a while."):
            try:
                output_dir = run_demucs(audio_file_path, model=model, device=device)
                st.success("Separation complete!")

                # List stem files and provide downloads
                stem_files = list(Path(output_dir).glob("*"))
                if stem_files:
                    st.write("Download separated stems:")
                    for stem_file in stem_files:
                        st.download_button(
                            label=stem_file.name,
                            data=open(stem_file, "rb").read(),
                            file_name=stem_file.name,
                            mime="audio/wav",
                        )
                else:
                    st.warning("No stems found in output.")

            except Exception as e:
                st.error(f"Error during separation: {e}")

# Cleanup temp files on rerun
def cleanup():
    for f in temp_files:
        try:
            os.remove(f)
        except Exception:
            pass

st.cache_data.clear()  # Optional: clear cached data on rerun (Streamlit 1.20+)
st.experimental_refresh()

cleanup()
