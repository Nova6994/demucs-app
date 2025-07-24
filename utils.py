# utils.py

import os
import sys
import subprocess
import tempfile
from pathlib import Path
import yt_dlp
import ffmpeg_downloader

# Install ffmpeg and get its path
ffmpeg_downloader.install()
ffmpeg_path = ffmpeg_downloader.utils.get_ffmpeg_path()

if not ffmpeg_path or not Path(ffmpeg_path).exists():
    raise RuntimeError("FFmpeg installation failed or ffmpeg binary not found.")

# Add ffmpeg folder to PATH for yt-dlp and subprocess calls
os.environ["PATH"] = str(Path(ffmpeg_path).parent) + os.pathsep + os.environ.get("PATH", "")

def download_youtube_audio(url, ffmpeg_path=None):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
            output_path = tmpfile.name

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = str(Path(ffmpeg_path).parent)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return output_path
    except Exception as e:
        raise RuntimeError(f"Failed to download audio from YouTube: {e}")

def run_demucs(audio_path, model='htdemucs', device='cpu'):
    output_dir = tempfile.mkdtemp()
    command = [
        sys.executable, "-m", "demucs",
        "--model", model,
        "--out", output_dir,
        "--device", device,
        audio_path
    ]

    # If using 4-stem model, add two-stems vocals option
    if model == "htdemucs":
        command.insert(3, "--two-stems")
        command.insert(4, "vocals")

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Demucs failed: {e}")
    except FileNotFoundError:
        raise RuntimeError("Demucs not found. Make sure Demucs is installed and accessible.")

    # Locate Demucs output folder
    for root, dirs, _ in os.walk(output_dir):
        for d in dirs:
            if d.startswith(model):
                return os.path.join(output_dir, d)

    raise RuntimeError("Demucs output not found.")


