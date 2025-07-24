import os
import tempfile
import urllib.request
import tarfile
import shutil
from pathlib import Path
import yt_dlp

# Directory to store static ffmpeg binaries
FFMPEG_DIR = Path(tempfile.gettempdir()) / "ffmpeg_static"

def download_ffmpeg():
    if (FFMPEG_DIR / "ffmpeg").exists() and (FFMPEG_DIR / "ffprobe").exists():
        # ffmpeg already downloaded
        return

    FFMPEG_DIR.mkdir(parents=True, exist_ok=True)

    # Static ffmpeg build URL for Linux AMD64 - adjust if needed for other OSes
    ffmpeg_url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"

    archive_path = FFMPEG_DIR / "ffmpeg.tar.xz"
    urllib.request.urlretrieve(ffmpeg_url, archive_path)

    # Extract the tar.xz archive
    with tarfile.open(archive_path) as tar:
        tar.extractall(path=FFMPEG_DIR)

    # Find extracted folder (something like ffmpeg-*-amd64-static)
    extracted_folder = next(
        (f for f in FFMPEG_DIR.iterdir() if f.is_dir() and "ffmpeg" in f.name and "static" in f.name),
        None
    )
    if not extracted_folder:
        raise RuntimeError("Failed to find extracted ffmpeg folder")

    # Move ffmpeg and ffprobe binaries to FFMPEG_DIR root
    shutil.move(str(extracted_folder / "ffmpeg"), str(FFMPEG_DIR / "ffmpeg"))
    shutil.move(str(extracted_folder / "ffprobe"), str(FFMPEG_DIR / "ffprobe"))

    # Clean up extracted folder and archive
    shutil.rmtree(extracted_folder)
    archive_path.unlink()

def download_youtube_audio(url):
    download_ffmpeg()  # Ensure ffmpeg is downloaded

    ffmpeg_path = str(FFMPEG_DIR.resolve())

    # Add ffmpeg_path to PATH environment variable so yt-dlp finds ffmpeg and ffprobe
    env = os.environ.copy()
    env["PATH"] = ffmpeg_path + os.pathsep + env.get("PATH", "")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(tempfile.gettempdir(), "%(id)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "ffmpeg_location": ffmpeg_path,  # Tell yt-dlp where ffmpeg binaries are
        # Passing environment so subprocesses inherit the PATH with ffmpeg
        "env": env,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        # The postprocessor changes extension to .mp3
        if not filename.endswith(".mp3"):
            filename = filename.rsplit(".", 1)[0] + ".mp3"
        return filename

# Add your run_demucs or other functions below...
