# demucsapp.py

import streamlit as st
import os
from pathlib import Path
import tempfile
from utils import download_youtube_audio, run_demucs
import imageio_ffmpeg
import subprocess

# -- Page config and style --

st.set_page_config(page_title="🎧 Demucs Audio Stem Splitter", layout="wide")

# Add custom CSS for nicer buttons and layout
st.markdown("""
<style>
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        height: 3em;
        width: 100%;
        font-size: 1.1em;
        border-radius: 10px;
    }
    .stButton > button:hover {
        background-color: #45a049;
        color: #fff;
    }
    .sidebar .sidebar-content {
        background: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    .main .block-container {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎧 Audio Stem Splitter")
st.caption("Powered by Demucs + Streamlit")

# Show ffmpeg version for debug
ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
st.text(f"Using FFmpeg binary from: {ffmpeg_bin}")
try:
    ffmpeg_version = subprocess.run([ffmpeg_bin, "-version"], capture_output=True, text=True, check=True)
    st.text_area("FFmpeg Version", ffmpeg_version.stdout, height=100)
except Exception as e:
    st.error(f"Failed to run ffmpeg: {e}")

# -- Sidebar for settings --

st.sidebar.header("Separation Settings")
stem_choice = st.sidebar.selectbox(
    "Choose stem model",
    ["4-stem (Vocals, Drums, Bass, Other)", "6-stem (Vocals, Drums, Bass, Piano, Guitar, Other)"]
)
model = "htdemucs" if "4-stem" in stem_choice else "htdemucs_6s"

device_choice = st.sidebar.selectbox(
    "Select compute device",
    ["cpu", "cuda (GPU)"]
)
device = "cuda" if "cuda" in device_choice else "cpu"

# -- Main UI --

st.subheader("1. Upload Audio or Provide YouTube Link")

input_method = st.radio("Select input type:", ["YouTube Link", "Upload Audio File"])

audio_path = None

if input_method == "YouTube Link":
    youtube_url = st.text_input("Enter YouTube URL:")
    if youtube_url:
        try:
            with st.spinner("Downloading audio from YouTube..."):
                audio_path = download_youtube_audio(youtube_url)
            st.success("YouTube audio downloaded successfully!")
        except Exception as e:
            st.error(f"Error downloading YouTube audio: {e}")

elif input_method == "Upload Audio File":
    uploaded_file = st.file_uploader("Upload audio file (WAV, MP3, FLAC)", type=["wav", "mp3", "flac"])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.read())
            audio_path = tmp_file.name
        st.success(f"Uploaded file saved as {Path(audio_path).name}")

# -- Process and separate --

if audio_path:
    if st.button("🔍 Separate Stems"):
        with st.spinner("Running Demucs... this might take a minute"):
            try:
                output_folder = run_demucs(audio_path, model=model, device=device)
                st.success("Separation complete! Download your stems below:")

                # List and play stems with download buttons
                for stem_file in sorted(os.listdir(output_folder)):
                    if stem_file.lower().endswith(".wav"):
                        file_path = os.path.join(output_folder, stem_file)
                        st.audio(file_path)
                        with open(file_path, "rb") as f:
                            st.download_button(label=f"Download {stem_file}", data=f, file_name=stem_file)

            except Exception as e:
                st.error(f"Error during Demucs separation: {e}")
