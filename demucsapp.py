import streamlit as st
from utils import download_youtube_audio, run_demucs
import os
import shutil

st.set_page_config(page_title="🎵 Demucs Stem Separator", layout="wide")

st.title("🎵 Demucs Stem Separator Web App")
st.markdown("""
Upload an audio file or provide a YouTube URL.  
The app will separate the audio into stems using Demucs.  
Powered by Streamlit and Demucs.
""")

model = st.selectbox("Select Demucs Model", options=["htdemucs", "demucs"], index=0)
device = st.selectbox("Device", options=["cpu", "cuda"], index=0)

input_type = st.radio("Input type", options=["Upload Audio File", "YouTube URL"])

audio_path = None
temp_files = []

if input_type == "Upload Audio File":
    uploaded_file = st.file_uploader("Choose audio file", type=["mp3", "wav", "m4a", "flac", "ogg"])
    if uploaded_file:
        temp_file = f"temp_{uploaded_file.name}"
        with open(temp_file, "wb") as f:
            f.write(uploaded_file.getbuffer())
        audio_path = temp_file
        temp_files.append(temp_file)

else:
    yt_url = st.text_input("Enter YouTube URL")
    if yt_url:
        with st.spinner("Downloading audio from YouTube..."):
            try:
                audio_path = download_youtube_audio(yt_url)
                temp_files.append(audio_path)
                st.success("Downloaded YouTube audio successfully!")
            except Exception as e:
                st.error(f"Failed to download YouTube audio: {e}")

if audio_path:
    if st.button("Run Demucs Separation"):
        with st.spinner("Separating stems... This may take a while."):
            try:
                output_folder = run_demucs(audio_path, model=model, device=device)
                st.success("Separation complete!")
                
                # List the separated stems files and let user play/download them
                stems = [f for f in os.listdir(output_folder) if os.path.isfile(os.path.join(output_folder, f))]
                st.subheader("Separated Stems:")
                for stem_file in stems:
                    stem_path = os.path.join(output_folder, stem_file)
                    st.audio(stem_path)
                    with open(stem_path, "rb") as f:
                        st.download_button(label=f"Download {stem_file}", data=f, file_name=stem_file)
            except Exception as e:
                st.error(f"Demucs separation failed: {e}")

# Cleanup temp files on rerun or exit
def cleanup():
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)

st.experimental_singleton.clear()
cleanup()
