# utils.py

import os
import subprocess
import tempfile
from pathlib import Path
import yt_dlp


def download_youtube_audio(url):
    """
    Downloads audio from a YouTube URL using yt-dlp.
    Returns the path to the downloaded audio file.
    """
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "%(title).80s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    files = os.listdir(temp_dir)
    for file in files:
        if file.endswith(".mp3"):
            return os.path.join(temp_dir, file)
    raise FileNotFoundError("Failed to download or convert audio.")


def run_demucs(audio_path, model, device="cpu"):
    """
    Runs the Demucs stem separation on the provided audio file.
    Returns the path to the folder containing separated stems.
    """
    output_dir = tempfile.mkdtemp()
    command = [
        "python3" if os.name != "nt" else "python",
        "-m", "demucs",
        audio_path,
        "--two-stems=vocals" if model == "htdemucs" else "",
        "--model", model,
        "--out", output_dir,
        "--device", device
    ]
    # Clean out empty strings from command
    command = [arg for arg in command if arg]

    subprocess.run(command, check=True)
    # Demucs outputs to a folder with the original file name
    base_name = Path(audio_path).stem
    return os.path.join(output_dir, model, base_name)
