# utils.py

import os
import subprocess
import tempfile
from pathlib import Path
import yt_dlp
import imageio_ffmpeg

def download_youtube_audio(url):
    """
    Downloads audio from a YouTube URL and returns the path to the downloaded mp3 file.
    """
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
        # Tell yt_dlp to use the imageio_ffmpeg's ffmpeg binary
        'ffmpeg_location': os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    if not Path(output_path).exists():
        raise RuntimeError("Failed to download or convert YouTube audio.")

    return output_path

def run_demucs(audio_path, model='htdemucs', device='cpu'):
    """
    Runs Demucs stem separation on the given audio file.
    Returns path to folder containing separated stems.
    Raises RuntimeError on failure.
    """
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Input audio file not found: {audio_path}")

    output_dir = tempfile.mkdtemp(prefix="demucs_out_")

    command = [
        "python", "-m", "demucs",
        "--model", model,
        "--out", output_dir,
        "--device", device,
        audio_path
    ]

    # Add two-stem option for 4-stem model (vocals + rest)
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

    # Find folder with separated stems
    for root, dirs, files in os.walk(output_dir):
        for d in dirs:
            if d.startswith(model):
                return os.path.join(output_dir, d)

    raise RuntimeError("Could not find Demucs output directory.")
