# demucsapp.py

import streamlit as st
import os
from pathlib import Path
from utils import download_youtube_audio, run_demucs

# Streamlit page config
st.set_page_config(page_title="Demucs Stem Splitter", layout="centered")
st.title("🎧 Audio Stem Splitter")
st.caption("Powered by Demucs + Streamlit")

# Sidebar options
st.sidebar.header("Separation Settings")
stem_type = st.sidebar.selectbox("Choose stem model", ["4-stem (Vocals, Drums, Bass, Other)", "6-stem (Vocals, Drums, Bass, Piano, Guitar, Other)"])
model = "htdemucs" if "4-stem" in stem_type else "htdemucs_6s"
device = st.sidebar.selectbox("Compute device", ["cpu", "cuda (GPU)"])

st.subheader("1. Upload or Provide YouTube Link")

# Input type selection
option = st.radio("Select input type:", ["YouTube Link", "Upload File"])

audio_path = None

if option == "YouTube Link":
    youtube_url = st.text_input("Enter YouTube URL:")
    if youtube_url:
        with st.spinner("Downloading from YouTube..."):
            try:
                audio_path = download_youtube_audio(youtube_url)
                st.success("Download complete!")
            except Exception as e:
                st.error(f"Download failed: {e}")

elif option == "Upload File":
    uploaded_file = st.file_uploader("Upload audio file (WAV/MP3/FLAC)", type=["wav", "mp3", "flac"])
    if uploaded_file:
        with open("temp_audio" + Path(uploaded_file.name).suffix, "wb") as f:
            f.write(uploaded_file.getbuffer())
        audio_path = os.path.abspath("temp_audio" + Path(uploaded_file.name).suffix)
        st.success(f"Uploaded file saved: {Path(audio_path).name}")

if audio_path and st.button("🔍 Separate Stems"):
    with st.spinner("Running Demucs... this may take a minute"):
        try:
            output_folder = run_demucs(audio_path, model=model, device="cuda" if "cuda" in device else "cpu")
            st.success("Stems successfully separated!")
            st.markdown("### 🎼 Download Separated Stems")
            for file in os.listdir(output_folder):
                if file.endswith(".wav"):
                    audio_file = os.path.join(output_folder, file)
                    st.audio(audio_file)
                    with open(audio_file, "rb") as f:
                        st.download_button(f"Download {file}", f, file_name=file)
        except Exception as e:
            st.error(f"Demucs failed: {e}")
