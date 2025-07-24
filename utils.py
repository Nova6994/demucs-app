import os
import tempfile
import yt_dlp
import requests
import zipfile
import platform
import subprocess
from pathlib import Path

# --- Download and prepare static ffmpeg binaries for web environment ---
FFMPEG_DIR = Path(tempfile.gettempdir()) / "ffmpeg-static"
FFMPEG_BIN = FFMPEG_DIR / "ffmpeg"
FFPROBE_BIN = FFMPEG_DIR / "ffprobe"

def download_ffmpeg_static():
    if FFMPEG_BIN.exists() and FFPROBE_BIN.exists():
        return  # already downloaded

    FFMPEG_DIR.mkdir(exist_ok=True)

    system = platform.system()
    if system == "Linux":
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        archive_path = FFMPEG_DIR / "ffmpeg.tar.xz"
        r = requests.get(url, stream=True)
        with open(archive_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        # Extract only ffmpeg and ffprobe binaries from tar.xz
        import tarfile
        with tarfile.open(archive_path, "r:xz") as tar:
            members = [m for m in tar.getmembers() if m.name.endswith(('ffmpeg', 'ffprobe'))]
            for member in members:
                member.name = Path(member.name).name  # strip folder
                tar.extract(member, FFMPEG_DIR)
        archive_path.unlink()
    elif system == "Darwin":
        # macOS static ffmpeg link - can be updated if needed
        url = "https://evermeet.cx/ffmpeg/ffmpeg.zip"
        archive_path = FFMPEG_DIR / "ffmpeg.zip"
        r = requests.get(url)
        with open(archive_path, "wb") as f:
            f.write(r.content)
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(FFMPEG_DIR)
        archive_path.unlink()
    elif system == "Windows":
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        archive_path = FFMPEG_DIR / "ffmpeg.zip"
        r = requests.get(url)
        with open(archive_path, "wb") as f:
            f.write(r.content)
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            # Extract to FFMPEG_DIR, binaries usually in 'ffmpeg-xxx/bin'
            zip_ref.extractall(FFMPEG_DIR)
        archive_path.unlink()
    else:
        raise RuntimeError(f"Unsupported OS for ffmpeg static download: {system}")

    # After extraction, adjust FFMPEG_BIN and FFPROBE_BIN paths accordingly
    # For Linux and macOS, binaries are directly in FFMPEG_DIR
    # For Windows, need to find the bin folder
    if system == "Windows":
        # Find the first 'bin' folder inside FFMPEG_DIR and set bins there
        for root, dirs, files in os.walk(FFMPEG_DIR):
            if "ffmpeg.exe" in files and "ffprobe.exe" in files:
                global FFMPEG_BIN, FFPROBE_BIN
                FFMPEG_BIN = Path(root) / "ffmpeg.exe"
                FFPROBE_BIN = Path(root) / "ffprobe.exe"
                break

download_ffmpeg_static()

# Set environment variable so yt_dlp and ffmpeg-python can find ffmpeg
os.environ["PATH"] = str(FFMPEG_DIR) + os.pathsep + os.environ.get("PATH", "")

def download_youtube_audio(url):
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
        # Explicitly set ffmpeg location for yt-dlp
        'ffmpeg_location': str(FFMPEG_DIR),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_path

def run_demucs(audio_path, model='htdemucs', device='cpu'):
    import demucs.apply
    import torch

    output_dir = tempfile.mkdtemp()

    # Load model
    model_obj = demucs.apply.load_model(name=model, device=device)

    # Separate audio
    demucs.apply.separate_file(
        model_obj,
        audio_path,
        output_dir,
        device=device,
        progress=True,
        two_stems=(model == 'htdemucs'),  # example conditional for two stems
    )

    # Demucs output folder is output_dir/<model_name>/<filename>_stem.wav
    output_subdir = Path(output_dir) / model
    if not output_subdir.exists():
        # Fallback to output_dir itself
        output_subdir = Path(output_dir)

    return str(output_subdir)
