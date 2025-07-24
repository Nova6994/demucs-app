# utils.py

import os
import sys
import subprocess
import tempfile
from pathlib import Path
import yt_dlp
import imageio_ffmpeg

# Get ffmpeg executable path from imageio-ffmpeg
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
if not Path(ffmpeg_path).exists():
    raise RuntimeError("FFmpeg binary not found by imageio-ffmpeg.")

# Add ffmpeg directory to PATH environment variable
os.environ["PATH"] = str(Path(ffmpeg_path).parent) + os.pathsep + os.environ.get("PATH", "")

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
            'ffmpeg_location': str(Path(ffmpeg_path).parent),
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return output_path
    except Exception as e:
        raise RuntimeError(f"Failed to download audio from YouTube: {e}")

def run_demucs(audio_path, model='htdemucs', device='cpu'):
    if not Path(audio_path).is_file():
        raise FileNotFoundError(f"Input audio file not found: {audio_path}")

    output_dir = tempfile.mkdtemp(prefix="demucs_out_")
    command = [
        sys.executable, "-m", "demucs",
        "--model", model,
        "--out", output_dir,
        "--device", device,
        audio_path
    ]

    # For 4-stem model, run two-stem mode (vocals + rest)
    if model == "htdemucs":
        command.insert(3, "--two-stems")
        command.insert(4, "vocals")

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Demucs failed with exit code {e.returncode}.\n"
            f"Stdout: {e.stdout}\nStderr: {e.stderr}"
        )
    except FileNotFoundError:
        raise RuntimeError("Demucs is not installed or not found in PATH.")

    # Find Demucs output folder
    for root, dirs, _ in os.walk(output_dir):
        for d in dirs:
            if d.startswith(model):
                return os.path.join(output_dir, d)

    raise RuntimeError("Could not find Demucs output directory.")
