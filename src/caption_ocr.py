"""
Caption OCR — Extraire le texte visible sur les frames video via pytesseract
"""
import subprocess
import tempfile
import os

from uniquifier import FFMPEG_BIN, FFPROBE_BIN


def get_duration(video_path):
    """Duree de la video en secondes"""
    if not FFPROBE_BIN:
        return 30
    try:
        cmd = [FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", video_path]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return float(r.stdout.strip())
    except Exception:
        return 30


def extract_text_from_video(video_path, num_frames=8):
    """Extraire le texte visible sur les frames video via OCR (pytesseract)"""
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        return []

    texts = []
    duration = get_duration(video_path)
    interval = max(1, int(duration / num_frames))

    with tempfile.TemporaryDirectory() as tmpdir:
        # Extraire des frames a intervalles reguliers
        cmd = [
            FFMPEG_BIN, "-i", video_path,
            "-vf", f"fps=1/{interval},scale=1080:-1",
            "-frames:v", str(num_frames),
            "-q:v", "2",
            os.path.join(tmpdir, "frame_%03d.jpg")
        ]
        subprocess.run(cmd, capture_output=True, timeout=60)

        for fname in sorted(os.listdir(tmpdir)):
            fpath = os.path.join(tmpdir, fname)
            try:
                img = Image.open(fpath)
                # OCR en francais + anglais
                text = pytesseract.image_to_string(img, lang='fra+eng')
                text = text.strip()
                if text and len(text) > 3:
                    texts.append(text)
            except Exception:
                continue

    # Deduplication
    seen = set()
    unique = []
    for t in texts:
        normalized = t.lower().strip()
        if normalized not in seen and len(normalized) > 3:
            seen.add(normalized)
            unique.append(t)

    return unique
