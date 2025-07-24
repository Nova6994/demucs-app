import os
import sys
import subprocess
import tempfile
import tarfile
import shutil
from pathlib import Path
import platform
import urllib.request
import yt_dlp

# Temp folder to hold ffmpeg static binaries
FFMPEG_DIR = Path(tempfile.gettempdir()) / "ffmpeg_static"

def download_ffmpeg():
    if (FFMPEG_DIR / "ffmpeg").exists() and (FFMPEG_DIR / "ffprobe").exists():
        return  # Already downloaded

    FFMPEG_DIR.mkdir(parents=True, exist_ok=True)

    system = platform.system()
    arch = platform.machine()

    # This URL is for Linux 64-bit static ffmpeg build with ffprobe included
    # For other OS, replace this URL with a suitable static build
    ffmpeg_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"

    archive_path = FFMPEG_DIR / "ffmpeg.tar.xz"

    print("Downloading static ffmpeg build...")
    urllib.request.urlretrieve(ffmpeg_url, archive_path)

    print("Extracting ffmpeg binaries...")
    with tarfile.open(archive_path) as tar:
        tar.extractall(path=FFMPEG_DIR)

    # The extracted folder is named like 'ffmpeg-*-amd64-static'
    extracted_folder = None
    for f in FFMPEG_DIR.iterdir():
        if f.is_dir() and "ffmpeg" in f.name and "static" in f.name:
            extracted_folder = f
            break

    if not extracted_folder:
        raise RuntimeError("Failed to find extracted ffmpeg folder")

    # Move ffmpeg and ffprobe to FFMPEG_DIR root
    shutil.move(str(extracted_folder / "ffmpeg"), str(FFMPEG_DIR / "ffmpeg"))
    shutil.move(str(extracted_folder / "ffprobe"), str(FFMPEG_DIR / "ffprobe"))

    # Clean up extracted folder and archive
    shutil.rmtree(extracted_folder)
    archive_path.unlink()
    print("ffmpeg static build ready.")

# Download on import / app startup
download_ffmpeg()

def download_youtube_audio(url):
    ffmpeg_path = str(FFMPEG_DIR)

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
            output_path = tmpfile.name

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "quiet": True,
            "noplaylist": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "ffmpeg_location": ffmpeg_path,
            "env": {**os.environ, "PATH": ffmpeg_path + os.pathsep + os.environ.get("PATH", "")},
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return output_path

    except Exception as e:
        raise RuntimeError(f"Failed to download audio from YouTube: {e}")

def run_demucs(audio_path, model="htdemucs", device="cpu"):
    output_dir = tempfile.mkdtemp(prefix="demucs_out_")

    command = [
        sys.executable, "-m", "demucs",
        "--model", model,
        "--out", output_dir,
        "--device", device,
        audio_path
    ]

    # Add two-stems option for 4-stem model only
    if model == "htdemucs":
        command.insert(3, "--two-stems")
        command.insert(4, "vocals")

    env = os.environ.copy()
    env["PATH"] = str(FFMPEG_DIR) + os.pathsep + env.get("PATH", "")

    try:
        subprocess.run(command, check=True, env=env)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Demucs failed: {e}")
    except FileNotFoundError:
        raise RuntimeError("Demucs is not installed or not found.")

    # Locate output folder with stems
    for root, dirs, _ in os.walk(output_dir):
        for d in dirs:
            if d.startswith(model):
                return os.path.join(output_dir, d)

    raise RuntimeError("Demucs output directory not found.")
