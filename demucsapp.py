#demucsapp.py

import streamlit as st
import subprocess
import os
import tempfile
from pathlib import Path
from utils import download_youtube_audio, run_demucs

# Page config
st.set_page_config(page_title="🎧 Demucs Stem Splitter", layout="wide", initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
    /* Center main title */
    .main-header {
        text-align: center;
        font-size: 3rem;
        font-weight: 700;
        color: #6C63FF;
        margin-bottom: 0.5rem;
    }
    /* Subtitle style */
    .subtitle {
        text-align: center;
        font-size: 1.25rem;
        color: #888888;
        margin-bottom: 2rem;
    }
    /* Sidebar header style */
    .sidebar .sidebar-content {
        background-color: #F0F2FF;
    }
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<h1 class="main-header">🎧 Demucs Stem Splitter</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Powered by Demucs + Streamlit — Separate vocals & instruments with ease</p>', unsafe_allow_html=True)

# Sidebar controls with explanations and icons
with st.sidebar:
    st.header("⚙️ Separation Settings")
    stem_type = st.selectbox(
        "Choose stem model:",
        ["🎤 4-stem (Vocals, Drums, Bass, Other)", "🎸 6-stem (Vocals, Drums, Bass, Piano, Guitar, Other)"]
    )
    model = "htdemucs" if "4-stem" in stem_type else "htdemucs_6s"

    device = st.radio(
        "Compute device:",
        ("🖥 CPU (Slower)", "⚡ GPU (Faster, if available)")
    )
    device_flag = "cpu" if "CPU" in device else "cuda"

st.markdown("## 1️⃣ Upload or Paste YouTube Link")

option = st.radio("Select input type:", ["📺 YouTube Link", "🎵 Upload Audio File"])

audio_path = None

if option == "📺 YouTube Link":
    youtube_url = st.text_input("Paste YouTube URL here:")
    if youtube_url:
        with st.spinner("⬇️ Downloading audio..."):
            try:
                audio_path = download_youtube_audio(youtube_url)
                st.success("✅ Download complete!")
            except Exception as e:
                st.error(f"❌ Download failed: {e}")

elif option == "🎵 Upload Audio File":
    uploaded_file = st.file_uploader("Upload your audio file (wav, mp3, flac):", type=["wav", "mp3", "flac"])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.read())
            audio_path = tmp_file.name
        st.success(f"✅ Uploaded file saved: {Path(audio_path).name}")

if audio_path:
    st.markdown("## 2️⃣ Separate the Stems")
    if st.button("🎚 Separate Stems"):
        with st.spinner("🔄 Processing with Demucs... this may take a bit"):
            try:
                output_folder = run_demucs(audio_path, model, device=device_flag)
                st.success("🎉 Separation complete! Download your stems below:")
                # Show audio players and download buttons
                for stem_file in sorted(os.listdir(output_folder)):
                    if stem_file.endswith(".wav"):
                        file_path = os.path.join(output_folder, stem_file)
                        st.audio(file_path)
                        with open(file_path, "rb") as f:
                            st.download_button(f"Download {stem_file}", f, file_name=stem_file)
            except Exception as e:
                st.error(f"❌ Demucs failed: {e}")

st.markdown("---")
st.markdown("Made with ❤️ by [Your Name]")
