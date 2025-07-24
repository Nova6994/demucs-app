import streamlit as st
import os
import tempfile
from pathlib import Path
from utils import download_youtube_audio, run_demucs

st.set_page_config(page_title="🎧 Demucs Stem Splitter", layout="centered")
st.title("🎧 Audio Stem Splitter")
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #1DB954;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 24px;
        margin-top: 12px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #17a34a;
        cursor: pointer;
    }
    .stRadio>div {
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True
)

st.sidebar.header("Separation Settings")
stem_type = st.sidebar.selectbox(
    "Choose stem model",
    ["4-stem (Vocals, Drums, Bass, Other)", "6-stem (Vocals, Drums, Bass, Piano, Guitar, Other)"]
)
model = "htdemucs" if "4-stem" in stem_type else "htdemucs_6s"

device = st.sidebar.selectbox("Compute device", ["cpu", "cuda (GPU)"])

st.subheader("1. Upload or Provide YouTube Link")
option = st.radio("Select input type:", ["YouTube Link", "Upload File"])

audio_path = None

if option == "YouTube Link":
    youtube_url = st.text_input("Enter YouTube URL:")
    if youtube_url:
        try:
            with st.spinner("Downloading audio from YouTube..."):
                audio_path = download_youtube_audio(youtube_url)
            st.success("YouTube audio downloaded successfully!")
        except Exception as e:
            st.error(f"Download failed: {e}")

elif option == "Upload File":
    uploaded_file = st.file_uploader("Upload audio file (WAV/MP3/FLAC)", type=["wav", "mp3", "flac"])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.read())
            audio_path = tmp_file.name
        st.success(f"Uploaded file saved: {Path(audio_path).name}")

if audio_path:
    if st.button("🔍 Separate Stems"):
        try:
            with st.spinner("Running Demucs, please wait... This may take a few minutes"):
                output_folder = run_demucs(audio_path, model=model, device="cuda" if "cuda" in device else "cpu")
            st.success("Separation complete! Listen and download below:")

            st.markdown("### 🎼 Separated Stems")
            stem_files = [f for f in os.listdir(output_folder) if f.endswith(".wav")]
            for stem_file in stem_files:
                stem_path = os.path.join(output_folder, stem_file)
                st.audio(stem_path)
                with open(stem_path, "rb") as f:
                    st.download_button(label=f"Download {stem_file}", data=f, file_name=stem_file)
        except Exception as e:
            st.error(f"Error during separation: {e}")
else:
    st.info("Provide a YouTube link or upload an audio file to get started.")
