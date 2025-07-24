import os
import sys
import subprocess
import tempfile
from pathlib import Path
import yt_dlp
import imageio_ffmpeg

# Get ffmpeg executable path from imageio-ffmpeg
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = str(Path(ffmpeg_path).parent)

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
            'ffmpeg_location': ffmpeg_dir,  # Explicitly tell yt-dlp where ffmpeg lives
            # Also set env for subprocesses
            'env': {**os.environ, "PATH": ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")},
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

    if model == "htdemucs":
        command.insert(3, "--two-stems")
        command.insert(4, "vocals")

    # Prepare environment for subprocess: ensure ffmpeg in PATH
    env = os.environ.copy()
    env["PATH"] = ffmpeg_dir + os.pathsep + env.get("PATH", "")

    try:
        subprocess.run(command, check=True, env=env)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Demucs failed with exit code {e.returncode}.\nStdout: {e.stdout}\nStderr: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("Demucs not found in PATH or not installed.")

    # Locate Demucs output folder
    for root, dirs, _ in os.walk(output_dir):
        for d in dirs:
            if d.startswith(model):
                return os.path.join(output_dir, d)

    raise RuntimeError("Demucs output directory not found.")
