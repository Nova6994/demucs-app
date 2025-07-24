import streamlit as st
import os
from pathlib import Path
import tempfile
from utils import download_youtube_audio, run_demucs
import imageio_ffmpeg

# Set ffmpeg path from imageio_ffmpeg
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
os.environ["PATH"] = str(Path(ffmpeg_path).parent) + os.pathsep + os.environ.get("PATH", "")

# --- Streamlit UI ---
st.set_page_config(page_title="Demucs Stem Splitter", layout="centered")
st.title("🎧 Audio Stem Splitter")
st.caption("Powered by Demucs + Streamlit")

# Custom CSS for nicer UI
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

# Sidebar: model & device
st.sidebar.header("Separation Settings")
stem_type = st.sidebar.selectbox("Choose stem model", ["4-stem (Vocals, Drums, Bass, Other)", "6-stem (Vocals, Drums, Bass, Piano, Guitar, Other)"])
model = "htdemucs" if "4-stem" in stem_type else "htdemucs_6s"
device = st.sidebar.selectbox("Compute device", ["cpu", "cuda (GPU)"])

st.subheader("1. Upload or Provide YouTube Link")
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
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as temp_file:
            temp_file.write(uploaded_file.read())
            audio_path = temp_file.name
        st.success(f"Uploaded file saved: {Path(audio_path).name}")

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
