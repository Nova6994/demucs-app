import streamlit as st
import yt_dlp
import subprocess
import os

st.title("YouTube Audio Stem Separator")

# Input for YouTube URL
youtube_url = st.text_input("Enter YouTube URL")

# Model choice: 4-stem or 6-stem
model_choice = st.selectbox("Choose separation model", ("htdemucs_4s", "htdemucs_6s"))

if st.button("Download & Separate"):
    if not youtube_url:
        st.error("Please enter a YouTube URL.")
    else:
        try:
            st.info("Downloading audio from YouTube...")
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloaded_song.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            audio_file = "downloaded_song.wav"
            if not os.path.exists(audio_file):
                st.error("Failed to download audio file.")
                st.stop()
            st.success("Audio downloaded!")

            st.info(f"Separating stems using model: {model_choice} ...")
            # Run Demucs on CPU
            subprocess.run([
                "demucs",
                "-d", "cpu",
                "-n", model_choice,
                audio_file
            ], check=True)
            st.success("Separation complete!")

            # Inform user where files are saved
            output_dir = os.path.join("separated", model_choice)
            st.write(f"Separated stems are saved in `{output_dir}` folder.")

        except Exception as e:
            st.error(f"An error occurred: {e}")

# Footer
st.markdown("---")
st.caption("Built with ❤️ using Demucs and Streamlit.")