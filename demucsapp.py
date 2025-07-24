# demucsapp.py

import streamlit as st
import subprocess
import os
import tempfile
from pathlib import Path
import ffmpeg_downloader
from utils import download_youtube_audio, run_demucs

# Automatically download and configure ffmpeg
ffmpeg_downloader.download_ffmpeg()
ffmpeg_path = ffmpeg_downloader.utils.get_ffmpeg_path()
os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ["PATH"]

# Page config
st.set_page_config(page_title="Demucs Stem Splitter", layout="centered")
st.title("🎧 Audio Stem Splitter")
st.caption("Powered by Demucs + Streamlit")

# Sidebar Options
st.sidebar.header("Separation Settings")
stem_type = st.sidebar.selectbox("Choose stem model", ["4-stem (Vocals, Drums, Bass, Other)", "6-stem (Vocals, Drums, Bass, Piano, Guitar, Other)"])
model = "htdemucs" if "4-stem" in stem_type else "htdemucs_6s"
device = st.sidebar.selectbox("Compute device", ["cpu", "cuda (GPU)"])

st.subheader("1. Upload or Provide YouTube Link")

# Audio source options
option = st.radio("Select input type:", ["YouTube Link", "Upload File"])

audio_path = None

if option == "YouTube Link":
    youtube_url = st.text_input("Enter YouTube URL:")
    if youtube_url:
        with st.spinner("Downloading from YouTube..."):
            try:
                audio_path = download_youtube_audio(youtube_url, ffmpeg_path)
                st.success("Download complete!")
            except Exception as e:
                st.error(f"Download failed: {e}")
elif option == "Upload File":
    uploaded_file = st.file_uploader("Upload audio file (WAV/MP3/FLAC)", type=["wav", "mp3", "flac"])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as temp_file:
            temp_file.write(uploaded_file.read())
            audio_path = temp_file.name
        st.success(f"Uploaded file saved: {Path(audio_path).name}")

# Process with Demucs
if audio_path and st.button("🔍 Separate Stems"):
    with st.spinner("Running Demucs... this may take a minute"):
        try:
            output_folder = run_demucs(audio_path, model, device="cuda" if "cuda" in device else "cpu")
            st.success("Stems successfully separated!")
            st.markdown("### 🎼 Download Separated Stems")
            for file in os.listdir(output_folder):
                if file.endswith(".wav"):
                    st.audio(os.path.join(output_folder, file))
                    with open(os.path.join(output_folder, file), "rb") as f:
                        st.download_button("Download " + file, f, file_name=file)
        except Exception as e:
            st.error(f"Demucs failed: {e}")

