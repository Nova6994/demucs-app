import os
import subprocess
import tempfile
from pathlib import Path
import yt_dlp
import imageio_ffmpeg

# Get ffmpeg binary path from imageio-ffmpeg (guaranteed to exist)
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = str(Path(ffmpeg_path).parent)

# Add ffmpeg directory to PATH environment variable
os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

def download_youtube_audio(url):
    """
    Download audio from YouTube URL as an mp3 to a temp file.
    Forces yt-dlp to use ffmpeg from imageio-ffmpeg.
    Returns the path to the downloaded mp3 file.
    """
    output_path = tempfile.mktemp(suffix=".mp3")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'noplaylist': True,
        'postprocessor_args': ['-nostdin'],  # prevents hangs
        'ffmpeg_location': ffmpeg_dir,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        raise RuntimeError(f"Failed to download audio from YouTube: {e}")

    return output_path

def run_demucs(audio_path, model='htdemucs', device='cpu'):
    """
    Run demucs separation on the given audio file.
    Returns the path to the folder containing separated stems.
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

    # For 4-stem model, enable two-stems vocals option
    if model == "htdemucs":
        command.insert(3, "--two-stems")
        command.insert(4, "vocals")

    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "PATH": ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")}
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Demucs failed with exit code {e.returncode}.\n"
            f"Stdout:\n{e.stdout}\nStderr:\n{e.stderr}"
        )
    except FileNotFoundError:
        raise RuntimeError("Demucs module not found or not installed.")

    # Locate output folder with separated stems
    for root, dirs, _ in os.walk(output_dir):
        for d in dirs:
            if d.startswith(model):
                return os.path.join(output_dir, d)

    raise RuntimeError("Demucs output folder not found.")
