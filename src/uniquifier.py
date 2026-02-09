"""
Video Uniquifier - Advanced anti-detection video modifications
Each modification can be toggled on/off via enabled_mods parameter.
Parallel batch processing with ThreadPoolExecutor.
"""
import subprocess
import os
import random
import string
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import locale

try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except:
    pass

INTENSITY_PRESETS = {
    "low": {
        "speed_range": (0.97, 1.03),
        "color_shift": 8,
        "crop_percent": 2,
        "noise_strength": 3,
        "zoom_range": (1.01, 1.03),
        "pitch_semitones": 0.3,
        "fps_shift": 0.03,
        "hflip_chance": 0.3,
    },
    "medium": {
        "speed_range": (0.94, 1.06),
        "color_shift": 15,
        "crop_percent": 3,
        "noise_strength": 5,
        "zoom_range": (1.02, 1.05),
        "pitch_semitones": 0.5,
        "fps_shift": 0.05,
        "hflip_chance": 0.4,
    },
    "high": {
        "speed_range": (0.88, 1.12),
        "color_shift": 22,
        "crop_percent": 4,
        "noise_strength": 8,
        "zoom_range": (1.03, 1.07),
        "pitch_semitones": 0.8,
        "fps_shift": 0.08,
        "hflip_chance": 0.5,
    }
}

# All mods enabled by default
DEFAULT_ENABLED = {
    "noise": True, "zoom": True, "gamma": True, "hue": True,
    "hflip": True, "crop": True, "speed": True,
    "pitch": True, "fps": True, "meta": True,
}

def uniquify_video_ffmpeg(input_path, output_path, intensity="medium", enabled_mods=None):
    """Applique des modifications anti-detection. Chaque mod peut etre desactivee."""
    preset = INTENSITY_PRESETS.get(intensity, INTENSITY_PRESETS["medium"])
    mods = {**DEFAULT_ENABLED, **(enabled_mods or {})}

    # === COMPUTE RANDOM VALUES (only for enabled mods) ===

    speed = 1.0
    if mods["speed"]:
        speed = random.uniform(*preset["speed_range"])

    hue_shift = 0
    saturation = 1.0
    if mods["hue"]:
        hue_shift = random.randint(-preset["color_shift"], preset["color_shift"])
        if abs(hue_shift) < 3:
            hue_shift = random.choice([-1, 1]) * random.randint(3, preset["color_shift"])
        saturation = random.uniform(0.94, 1.06)

    brightness = random.uniform(-0.03, 0.03)  # always subtle, part of encoding

    crop_pct = 0.0
    if mods["crop"]:
        crop_pct = random.uniform(0.5, preset["crop_percent"]) / 100

    zoom = 1.0
    if mods["zoom"]:
        zoom = random.uniform(*preset["zoom_range"])

    noise_strength = 0
    if mods["noise"]:
        noise_strength = random.uniform(1, preset["noise_strength"])

    do_hflip = False
    if mods["hflip"]:
        do_hflip = random.random() < preset["hflip_chance"]

    target_fps = 30.0
    if mods["fps"]:
        fps_shift = random.uniform(-preset["fps_shift"], preset["fps_shift"])
        target_fps = round(30 + fps_shift, 2)

    gamma = 1.0
    if mods["gamma"]:
        gamma = random.uniform(0.97, 1.03)

    pitch_semitones = 0.0
    if mods["pitch"]:
        pitch_semitones = random.uniform(-preset["pitch_semitones"], preset["pitch_semitones"])
        if abs(pitch_semitones) < 0.1:
            pitch_semitones = random.choice([-1, 1]) * random.uniform(0.1, preset["pitch_semitones"])

    # === BUILD VIDEO FILTER CHAIN ===
    filters = []

    # Speed
    if mods["speed"] and speed != 1.0:
        filters.append(f"setpts={1/speed}*PTS")

    # Crop (early = process fewer pixels later)
    if mods["crop"] and crop_pct > 0:
        filters.append(f"crop=iw*{1-crop_pct}:ih*{1-crop_pct}")

    # Zoom
    if mods["zoom"] and zoom > 1.0:
        filters.append(f"scale=iw*{zoom}:ih*{zoom}:flags=fast_bilinear")
        filters.append("crop=iw/{0}:ih/{0}".format(zoom))

    # Scale to output resolution
    filters.append("scale=1080:1920:force_original_aspect_ratio=decrease")
    filters.append("pad=1080:1920:(ow-iw)/2:(oh-ih)/2")

    # Hue + Saturation (after scale = fewer pixels)
    if mods["hue"]:
        filters.append(f"hue=h={hue_shift}:s={saturation}")

    # Brightness + Gamma combined in one eq filter
    if mods["gamma"] and gamma != 1.0:
        filters.append(f"eq=brightness={brightness}:gamma={gamma:.3f}")
    else:
        filters.append(f"eq=brightness={brightness}")

    # Flip
    if do_hflip:
        filters.append("hflip")

    # Noise
    if mods["noise"] and noise_strength > 0:
        filters.append(f"noise=alls={int(noise_strength)}:allf=t")

    # FPS
    if mods["fps"] and target_fps != 30.0:
        filters.append(f"fps={target_fps}")

    video_filter = ",".join(filters)

    # === AUDIO FILTERS ===
    audio_filters = []

    if mods["speed"] and 0.5 <= speed <= 2.0 and speed != 1.0:
        audio_filters.append(f"atempo={speed}")

    if mods["pitch"] and pitch_semitones != 0:
        pitch_factor = 2 ** (pitch_semitones / 12)
        audio_filters.append(f"asetrate=44100*{pitch_factor:.6f}")
        audio_filters.append("aresample=44100")

    audio_volume = random.uniform(0.97, 1.03)
    audio_filters.append(f"volume={audio_volume:.3f}")

    audio_filter = ",".join(audio_filters)

    # === ENCODING ===
    crf = random.randint(18, 24)
    gop_size = random.choice([24, 30, 48, 60, 72])
    bf_count = random.choice([0, 1, 2, 3])

    # === METADATA ===
    encoders = ["Lavf58.76.100", "Lavf59.27.100", "Lavf60.3.100", "HandBrake 1.6.1",
                "Adobe Premiere Pro", "DaVinci Resolve 18", "CapCut 3.2", "FFmpeg 6.0",
                "iMovie 10.3", "Final Cut Pro X", "Filmora 13", "VLC media player",
                "Adobe Media Encoder 2024", "Shotcut 24.01", "OpenShot 3.1"]
    handler_names = ["VideoHandler", "MainHandler", "ISO Media", "Apple Video Media Handler",
                     "Core Media Video", "GPAC ISO Video Handler", "Mainconcept Video Media Handler",
                     "L-SMASH Video Handler", "VideoHandle"]

    # === TRACK MODIFICATIONS ===
    modifications = {
        "speed": round(speed, 3),
        "hue_shift": hue_shift if mods["hue"] else 0,
        "saturation": round(saturation, 2),
        "brightness": round(brightness, 3),
        "crop_percent": round(crop_pct * 100, 1),
        "zoom": round(zoom, 3),
        "noise": round(noise_strength, 1),
        "hflip": do_hflip,
        "pitch_semitones": round(pitch_semitones, 2),
        "fps": target_fps,
        "gamma": round(gamma, 3),
        "crf": crf,
        "gop": gop_size,
        "metadata_randomized": mods["meta"],
    }

    # === BUILD COMMAND ===
    cmd = ["ffmpeg", "-y", "-i", input_path]
    cmd.extend(["-vf", video_filter])
    if audio_filter:
        cmd.extend(["-af", audio_filter])

    cmd.extend([
        "-c:v", "libx264", "-crf", str(crf), "-preset", "ultrafast",
        "-g", str(gop_size), "-bf", str(bf_count),
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
    ])

    # Metadata (only if enabled)
    if mods["meta"]:
        random_title = ''.join(random.choices(string.ascii_letters + string.digits + ' _-', k=random.randint(8, 32)))
        random_comment = ''.join(random.choices(string.ascii_letters + string.digits + ' .,!', k=random.randint(10, 48)))
        random_creation = (datetime.now() - timedelta(days=random.uniform(0, 30))).isoformat() + "Z"
        cmd.extend([
            "-metadata", f"title={random_title}",
            "-metadata", f"comment={random_comment}",
            "-metadata", f"encoder={random.choice(encoders)}",
            "-metadata", f"handler_name={random.choice(handler_names)}",
            "-metadata", f"creation_time={random_creation}",
            "-metadata", f"file_id={str(uuid.uuid4())}",
            "-metadata", f"major_brand=mp42",
            "-metadata", f"minor_version={random.randint(0, 512)}",
        ])

    cmd.append(output_path)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return {"success": True, "output_path": output_path, "modifications": modifications}
        else:
            return {"success": False, "error": result.stderr, "modifications": modifications}
    except Exception as e:
        return {"success": False, "error": str(e), "modifications": modifications}

def get_dated_folder_name():
    now = datetime.now()
    mois_fr = {
        1: "janvier", 2: "fevrier", 3: "mars", 4: "avril",
        5: "mai", 6: "juin", 7: "juillet", 8: "aout",
        9: "septembre", 10: "octobre", 11: "novembre", 12: "decembre"
    }
    return f"{now.day} {mois_fr[now.month]} {now.strftime('%Hh%M')}"

def _worker(args):
    """Worker pour le traitement parallele."""
    i, input_path, output_path, intensity, enabled_mods = args
    result = uniquify_video_ffmpeg(input_path, output_path, intensity, enabled_mods)
    result["variation"] = i + 1
    result["output_path"] = output_path
    return i, result

def batch_uniquify(input_path, output_dir, count=10, intensity="medium", enabled_mods=None):
    """Genere plusieurs variations en parallele (3-4x plus rapide)."""
    folder_name = get_dated_folder_name()
    dated_dir = os.path.join(output_dir, folder_name)
    os.makedirs(dated_dir, exist_ok=True)

    # Prepare tasks
    tasks = []
    for i in range(count):
        output_path = os.path.join(dated_dir, f"V{i+1:02d}.mp4")
        tasks.append((i, input_path, output_path, intensity, enabled_mods))

    # Run in parallel — max 3 workers to avoid overloading Streamlit Cloud
    max_workers = min(3, count)
    results = [None] * count

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_worker, task): task[0] for task in tasks}
        for future in as_completed(futures):
            idx, result = future.result()
            results[idx] = result

    return results

class VideoUniquifier:
    def __init__(self, intensity="medium"):
        self.intensity = intensity

    def uniquify(self, input_path, output_path, enabled_mods=None):
        return uniquify_video_ffmpeg(input_path, output_path, self.intensity, enabled_mods)
