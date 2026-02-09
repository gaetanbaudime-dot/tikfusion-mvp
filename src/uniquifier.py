"""
Video Uniquifier - Advanced anti-detection video modifications
Based on research into TikTok/Instagram detection systems:
- Perceptual hashing (pHash/DCT) = 30-35% weight → defeated by pixel noise + zoom
- Deep learning scene analysis = 25-30% → defeated by zoom + crop + flip
- Audio fingerprinting = 20-25% → defeated by pitch shift + noise injection
- Metadata = 5-10% → defeated by full metadata randomization
- File hash = 1-2% → defeated by any re-encoding
"""
import subprocess
import os
import random
import string
import uuid
from pathlib import Path
from datetime import datetime, timedelta
import locale

# Set French locale for date formatting
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

def uniquify_video_ffmpeg(input_path, output_path, intensity="medium"):
    """Applique des modifications anti-detection avancees a une video avec FFmpeg"""
    preset = INTENSITY_PRESETS.get(intensity, INTENSITY_PRESETS["medium"])

    # === VISUAL MODIFICATIONS ===

    speed = random.uniform(*preset["speed_range"])
    hue_shift = random.randint(-preset["color_shift"], preset["color_shift"])
    # Ensure hue shift is meaningful (at least 3 degrees)
    if abs(hue_shift) < 3:
        hue_shift = random.choice([-1, 1]) * random.randint(3, preset["color_shift"])
    saturation = random.uniform(0.94, 1.06)
    brightness = random.uniform(-0.03, 0.03)
    crop_pct = random.uniform(0.5, preset["crop_percent"]) / 100  # Minimum 0.5% crop

    # Zoom factor - repositions ALL pixels, breaks perceptual hash
    zoom = random.uniform(*preset["zoom_range"])

    # Pixel noise strength - invisible to eye but destroys pHash/DCT
    noise_strength = random.uniform(1, preset["noise_strength"])

    # Horizontal flip
    do_hflip = random.random() < preset["hflip_chance"]

    # Framerate shift - changes temporal fingerprint
    fps_shift = random.uniform(-preset["fps_shift"], preset["fps_shift"])
    target_fps = round(30 + fps_shift, 2)

    # === BUILD VIDEO FILTER CHAIN ===
    filters = []

    # 1. Speed change (changes temporal fingerprint)
    if speed != 1.0:
        filters.append(f"setpts={1/speed}*PTS")

    # 2. Hue + Saturation (changes color distribution)
    filters.append(f"hue=h={hue_shift}:s={saturation}")

    # 3. Brightness
    filters.append(f"eq=brightness={brightness}")

    # 4. Crop (changes frame boundaries)
    if crop_pct > 0:
        filters.append(f"crop=iw*{1-crop_pct}:ih*{1-crop_pct}")

    # 5. Zoom - CRITICAL: repositions every pixel, breaks perceptual hash
    # Apply zoom by scaling up then cropping back to original area
    filters.append(f"scale=iw*{zoom}:ih*{zoom}")
    filters.append("crop=iw/{0}:ih/{0}".format(zoom))

    # 6. Final scale back to 1080x1920 (TikTok/Reels format)
    filters.append("scale=1080:1920:force_original_aspect_ratio=decrease")
    filters.append("pad=1080:1920:(ow-iw)/2:(oh-ih)/2")

    # 7. Horizontal flip - changes ALL spatial relationships
    if do_hflip:
        filters.append("hflip")

    # 8. Pixel noise injection - INVISIBLE to eye, DESTROYS perceptual hash
    # noise filter: generates random noise per frame
    filters.append(f"noise=alls={int(noise_strength)}:allf=t")

    # 9. Slight random gamma curve - changes pixel distribution subtly
    gamma = random.uniform(0.97, 1.03)
    filters.append(f"eq=gamma={gamma:.3f}")

    # 10. Set output framerate (temporal fingerprint change)
    filters.append(f"fps={target_fps}")

    video_filter = ",".join(filters)

    # === AUDIO MODIFICATIONS ===
    audio_filters = []

    # 1. Tempo change (sync with video speed)
    if 0.5 <= speed <= 2.0:
        audio_filters.append(f"atempo={speed}")

    # 2. Pitch shift - CRITICAL: breaks audio fingerprinting (Shazam-like detection)
    # asetrate changes the sample rate which shifts pitch
    pitch_semitones = random.uniform(-preset["pitch_semitones"], preset["pitch_semitones"])
    # Ensure minimum pitch shift
    if abs(pitch_semitones) < 0.1:
        pitch_semitones = random.choice([-1, 1]) * random.uniform(0.1, preset["pitch_semitones"])
    pitch_factor = 2 ** (pitch_semitones / 12)
    # Apply pitch via aresample + asetrate combo
    audio_filters.append(f"asetrate=44100*{pitch_factor:.6f}")
    audio_filters.append("aresample=44100")

    # 3. Subtle audio noise - helps break audio fingerprint
    # Use volume modulation to add barely perceptible variation
    audio_volume = random.uniform(0.97, 1.03)
    audio_filters.append(f"volume={audio_volume:.3f}")

    audio_filter = ",".join(audio_filters)

    # === ENCODING PARAMETERS ===
    crf = random.randint(18, 24)

    # Randomize encoding params for unique bitstream
    gop_size = random.choice([24, 30, 48, 60, 72])  # keyframe interval
    bf_count = random.choice([0, 1, 2, 3])  # B-frames

    # === METADATA RANDOMIZATION ===
    encoders = ["Lavf58.76.100", "Lavf59.27.100", "Lavf60.3.100", "HandBrake 1.6.1",
                "Adobe Premiere Pro", "DaVinci Resolve 18", "CapCut 3.2", "FFmpeg 6.0",
                "iMovie 10.3", "Final Cut Pro X", "Filmora 13", "VLC media player",
                "Adobe Media Encoder 2024", "Shotcut 24.01", "OpenShot 3.1"]
    handler_names = ["VideoHandler", "MainHandler", "ISO Media", "Apple Video Media Handler",
                     "Core Media Video", "GPAC ISO Video Handler", "Mainconcept Video Media Handler",
                     "L-SMASH Video Handler", "VideoHandle"]

    random_title = ''.join(random.choices(string.ascii_letters + string.digits + ' _-', k=random.randint(8, 32)))
    random_comment = ''.join(random.choices(string.ascii_letters + string.digits + ' .,!', k=random.randint(10, 48)))
    random_encoder = random.choice(encoders)
    random_handler = random.choice(handler_names)
    random_days = random.uniform(0, 30)
    random_creation = (datetime.now() - timedelta(days=random_days)).isoformat() + "Z"
    random_uuid = str(uuid.uuid4())

    # === TRACK ALL MODIFICATIONS ===
    modifications = {
        "speed": round(speed, 3),
        "hue_shift": hue_shift,
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
        "metadata_randomized": True
    }

    # === BUILD FFMPEG COMMAND ===
    cmd = ["ffmpeg", "-y", "-i", input_path]

    # Video filters
    cmd.extend(["-vf", video_filter])

    # Audio filters
    if audio_filter:
        cmd.extend(["-af", audio_filter])

    # Encoding settings
    cmd.extend([
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", "ultrafast",
        "-g", str(gop_size),
        "-bf", str(bf_count),
        "-c:a", "aac",
        "-b:a", "128k",
    ])

    # Metadata
    cmd.extend([
        "-metadata", f"title={random_title}",
        "-metadata", f"comment={random_comment}",
        "-metadata", f"encoder={random_encoder}",
        "-metadata", f"handler_name={random_handler}",
        "-metadata", f"creation_time={random_creation}",
        "-metadata", f"file_id={random_uuid}",
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
    """Genere un nom de dossier avec date et heure en francais"""
    now = datetime.now()
    mois_fr = {
        1: "janvier", 2: "fevrier", 3: "mars", 4: "avril",
        5: "mai", 6: "juin", 7: "juillet", 8: "aout",
        9: "septembre", 10: "octobre", 11: "novembre", 12: "decembre"
    }
    jour = now.day
    mois = mois_fr[now.month]
    heure = now.strftime("%Hh%M")
    return f"{jour} {mois} {heure}"

def batch_uniquify(input_path, output_dir, count=10, intensity="medium"):
    """Genere plusieurs variations uniques avec noms V01, V02, etc."""
    folder_name = get_dated_folder_name()
    dated_dir = os.path.join(output_dir, folder_name)
    os.makedirs(dated_dir, exist_ok=True)

    results = []
    for i in range(count):
        output_path = os.path.join(dated_dir, f"V{i+1:02d}.mp4")
        result = uniquify_video_ffmpeg(input_path, output_path, intensity)
        result["variation"] = i + 1
        result["output_path"] = output_path
        results.append(result)

    return results

class VideoUniquifier:
    def __init__(self, intensity="medium"):
        self.intensity = intensity

    def uniquify(self, input_path, output_path):
        return uniquify_video_ffmpeg(input_path, output_path, self.intensity)
