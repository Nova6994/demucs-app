# utils.py

import os
import subprocess
import tempfile
from pathlib import Path
import yt_dlp
import ffmpeg_downloader

# Ensure ffmpeg is available and path is set
ffmpeg_downloader.install()
ffmpeg_path = ffmpeg_downloader.utils.get_ffmpeg_path()
os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ["PATH"]

FFMPEG_BIN = ffmpeg_path
FFPROBE_BIN = FFMPEG_BIN.replace('ffmpeg', 'ffprobe')

def download_youtube_audio(url, ffmpeg_path=None):
    output_path = tempfile.mktemp(suffix=".mp3")
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

    # Pass ffmpeg_location at top-level in ydl_opts
    if ffmpeg_path:
        ydl_opts['ffmpeg_location'] = os.path.dirname(ffmpeg_path)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_path

def run_demucs(audio_path, model='htdemucs', device='cpu'):
    output_dir = tempfile.mkdtemp()
    command = [
        "python", "-m", "demucs",
        "--model", model,
        "--out", output_dir,
        "--device", device,
        audio_path
    ]

    # Example: if you want 2 stems "vocals" for htdemucs
    if model == "htdemucs":
        command.insert(3, "--two-stems")
        command.insert(4, "vocals")

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Demucs failed: {e}")

    # Locate folder with separated files
    for root, dirs, files in os.walk(output_dir):
        for d in dirs:
            if d.startswith(model):
                return os.path.join(output_dir, d)

    raise RuntimeError("Demucs output not found.")
