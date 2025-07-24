# utils.py

import os
import sys
import subprocess
import tempfile
from pathlib import Path
import yt_dlp
import imageio_ffmpeg

# Get full path to ffmpeg binary from imageio-ffmpeg
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = str(Path(ffmpeg_path).parent)

# Add ffmpeg directory to PATH environment variable (optional but recommended)
os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

def download_youtube_audio(url):
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
            # Explicitly tell yt-dlp where ffmpeg and ffprobe are
            'ffmpeg_location': ffmpeg_dir,
            'ffprobe_location': ffmpeg_dir,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return output_path
    except Exception as e:
        raise RuntimeError(f"Failed to download audio from YouTube: {e}")

def run_demucs(audio_path, model='htdemucs', device='cpu'):
    output_dir = tempfile.mkdtemp(prefix="demucs_out_")
    command = [
        sys.executable, "-m", "demucs",
        "--model", model,
        "--out", output_dir,
        "--device", device,
        audio_path
    ]

    # Add two-stems option for 4-stem model (vocals + rest)
    if model == "htdemucs":
        command.insert(3, "--two-stems")
        command.insert(4, "vocals")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Demucs failed with exit code {e.returncode}.\n"
            f"Stdout: {e.stdout}\nStderr: {e.stderr}"
        )
    except FileNotFoundError:
        raise RuntimeError("Demucs is not installed or not found in PATH. Ensure 'python -m demucs' works in your environment.")

    # Find output folder created by Demucs
    for root, dirs, files in os.walk(output_dir):
        for d in dirs:
            if d.startswith(model):
                return os.path.join(output_dir, d)

    raise RuntimeError("Demucs output not found.")
