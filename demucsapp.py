import streamlit as st
import os
from pathlib import Path
from utils import download_youtube_audio, run_demucs
import tempfile

# Page config & style
st.set_page_config(page_title="🎧 Demucs Stem Splitter", layout="wide")
st.title("🎧 Audio Stem Splitter")
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1, h2, h3 {
        font-weight: 700;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
    }
    .stButton>button {
        background-color: #764ba2;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 24px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #5a3782;
    }
    </style>
    """, unsafe_allow_html=True
)

# Sidebar options
st.sidebar.header("Separation Settings")
stem_type = st.sidebar.selectbox(
    "Choose stem model",
    ["4-stem (Vocals, Drums, Bass, Other)", "6-stem (Vocals, Drums, Bass, Piano, Guitar, Other)"]
)
model = "htdemucs" if "4-stem" in stem_type else "htdemucs_6s"
device = st.sidebar.selectbox("Compute device", ["cpu", "cuda (GPU)"])

st.subheader("1. Upload Audio or Provide YouTube Link")

input_type = st.radio("Select input type:", ["YouTube Link", "Upload File"])

audio_path = None

if input_type == "YouTube Link":
    youtube_url = st.text_input("Enter YouTube URL:")
    if youtube_url:
        try:
            with st.spinner("Downloading audio from YouTube..."):
                audio_path = download_youtube_audio(youtube_url)
            st.success("YouTube audio downloaded successfully!")
        except Exception as e:
            st.error(f"Download failed: {e}")

elif input_type == "Upload File":
    uploaded_file = st.file_uploader("Upload audio file (WAV, MP3, FLAC)", type=["wav", "mp3", "flac"])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmpfile:
            tmpfile.write(uploaded_file.read())
            audio_path = tmpfile.name
        st.success(f"Uploaded file saved: {Path(audio_path).name}")

if audio_path:
    if st.button("🔍 Separate Stems"):
        with st.spinner("Running Demucs stem separation... this might take a minute"):
            try:
                output_folder = run_demucs(audio_path, model, device="cuda" if "cuda" in device else "cpu")
                st.success("Stem separation successful! 🎉")
                st.markdown("### 🎼 Listen & Download Separated Stems")
                for stem_file in os.listdir(output_folder):
                    if stem_file.endswith(".wav"):
                        stem_path = os.path.join(output_folder, stem_file)
                        st.audio(stem_path)
                        with open(stem_path, "rb") as f:
                            st.download_button(f"Download {stem_file}", f, file_name=stem_file)
            except Exception as e:
                st.error(f"Stem separation failed: {e}")
