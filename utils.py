import os
import sys
import subprocess
import tempfile
from pathlib import Path
import yt_dlp
import shutil

# Download static ffmpeg binaries and set environment variables for yt-dlp and subprocess
def setup_ffmpeg():
    import requests
    import zipfile

    ffmpeg_dir = Path(tempfile.gettempdir()) / "ffmpeg_static"
    if ffmpeg_dir.exists():
        return ffmpeg_dir

    url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    archive_path = ffmpeg_dir.parent / "ffmpeg-release-amd64-static.tar.xz"
    ffmpeg_dir.parent.mkdir(exist_ok=True)

    # Download ffmpeg archive
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(archive_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    # Extract
    import tarfile
    with tarfile.open(archive_path) as tar:
        tar.extractall(path=ffmpeg_dir.parent)

    # The extraction creates a folder like ffmpeg-<version>-amd64-static
    extracted_folder = next(ffmpeg_dir.parent.glob("ffmpeg-*-amd64-static"))
    # Rename/move to ffmpeg_static
    if ffmpeg_dir.exists():
        shutil.rmtree(ffmpeg_dir)
    extracted_folder.rename(ffmpeg_dir)

    return ffmpeg_dir

# Prepare ffmpeg and update PATH
ffmpeg_dir = setup_ffmpeg()
ffmpeg_bin_path = ffmpeg_dir / "ffmpeg"
ffprobe_bin_path = ffmpeg_dir / "ffprobe"
os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ.get("PATH", "")

def download_youtube_audio(url: str) -> str:
    """Download best audio from YouTube URL to a temp file using yt-dlp and static ffmpeg"""
    temp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    temp_audio.close()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_audio.name,
        'quiet': True,
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'ffmpeg_location': str(ffmpeg_dir),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return temp_audio.name

def run_demucs(audio_path: str, model="htdemucs", device="cpu") -> str:
    """Run Demucs model on the audio file, return output folder path"""
    output_dir = tempfile.mkdtemp(prefix="demucs_out_")

    command = [
        sys.executable, "-m", "demucs",
        "--model", model,
        "--out", output_dir,
        "--device", device,
        audio_path
    ]

    # Example: if you want 2-stem vocals + rest for htdemucs:
    if model == "htdemucs":
        command.insert(3, "--two-stems")
        command.insert(4, "vocals")

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Demucs failed: {e.stderr}")

    # Find Demucs output folder (starts with model name)
    for root, dirs, files in os.walk(output_dir):
        for d in dirs:
            if d.startswith(model):
                return os.path.join(root, d)

    raise RuntimeError("Demucs output folder not found")
