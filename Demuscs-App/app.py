import streamlit as st
import subprocess
import os
import tempfile
from pathlib import Path

st.set_page_config(page_title="Stem Splitter App", layout="centered")
st.title("🎛️ Stem Splitter using Demucs")
st.write("Split any song into separate stems (e.g., vocals, drums, bass) using Demucs. You can choose either 4-stem or 6-stem separation.")

# Model selection
stem_model = st.radio("Choose stem model:", options=["4-stem", "6-stem"], index=0)
model_name = "htdemucs" if stem_model == "4-stem" else "htdemucs_6s"

# Input method
method = st.radio("Input source:", ["Upload file", "YouTube link"], index=0)

audio_path = None

def separate_audio(input_file: Path):
    with st.spinner("Separating stems with Demucs..."):
        result = subprocess.run([
            "demucs",
            "-d", "cpu",
            "-n", model_name,
            str(input_file)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            st.error("Demucs failed:")
            st.code(result.stderr)
            return None

        return Path("separated") / model_name / input_file.stem

if method == "Upload file":
    uploaded_file = st.file_uploader("Upload a .wav or .mp3 file", type=["wav", "mp3"])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name[-4:]) as tmp:
            tmp.write(uploaded_file.read())
            audio_path = Path(tmp.name)

elif method == "YouTube link":
    yt_url = st.text_input("Enter YouTube URL")
    if yt_url:
        if st.button("Download and Process"):
            with st.spinner("Downloading from YouTube..."):
                try:
                    subprocess.run([
                        "yt-dlp",
                        "-x", "--audio-format", "wav",
                        "--no-playlist",
                        "-o", "yt_audio.%(ext)s",
                        yt_url
                    ], check=True)
                    audio_path = Path("yt_audio.wav")
                except subprocess.CalledProcessError as e:
                    st.error("Failed to download audio from YouTube")
                    st.code(e.stderr)

# Run separation if audio path is ready
if audio_path:
    output_dir = separate_audio(audio_path)
    if output_dir and output_dir.exists():
        st.success("Separation complete! Download stems below:")
        for stem in output_dir.iterdir():
            st.audio(stem)
            st.download_button(f"Download {stem.stem}", stem.read_bytes(), file_name=stem.name)

# Footer
st.markdown("---")
st.caption("Built with ❤️ using Demucs and Streamlit.")