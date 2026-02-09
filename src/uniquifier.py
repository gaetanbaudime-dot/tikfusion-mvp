"""
Video Uniquifier - Anti-detection video modifications
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
    "low": {"speed_range": (0.98, 1.02), "color_shift": 5, "crop_percent": 1},
    "medium": {"speed_range": (0.95, 1.05), "color_shift": 10, "crop_percent": 2},
    "high": {"speed_range": (0.90, 1.10), "color_shift": 20, "crop_percent": 3}
}

def uniquify_video_ffmpeg(input_path, output_path, intensity="medium"):
    """Applique des modifications uniques à une vidéo avec FFmpeg"""
    preset = INTENSITY_PRESETS.get(intensity, INTENSITY_PRESETS["medium"])
    
    speed = random.uniform(*preset["speed_range"])
    hue_shift = random.randint(-preset["color_shift"], preset["color_shift"])
    saturation = random.uniform(0.95, 1.05)
    brightness = random.uniform(-0.02, 0.02)
    crop_pct = random.uniform(0, preset["crop_percent"]) / 100
    
    filters = []
    
    if speed != 1.0:
        filters.append(f"setpts={1/speed}*PTS")
    
    filters.append(f"hue=h={hue_shift}:s={saturation}")
    filters.append(f"eq=brightness={brightness}")
    
    if crop_pct > 0:
        filters.append(f"crop=iw*{1-crop_pct}:ih*{1-crop_pct}")
        filters.append("scale=1080:1920:force_original_aspect_ratio=decrease")
        filters.append("pad=1080:1920:(ow-iw)/2:(oh-ih)/2")
    
    do_hflip = random.random() < 0.2
    if do_hflip:
        filters.append("hflip")

    video_filter = ",".join(filters)
    audio_filter = f"atempo={speed}" if 0.5 <= speed <= 2.0 else ""

    crf = random.randint(18, 23)

    # Randomiser les métadonnées pour renforcer l'unicité (max différence entre variations)
    encoders = ["Lavf58.76.100", "Lavf59.27.100", "Lavf60.3.100", "HandBrake 1.6.1",
                "Adobe Premiere Pro", "DaVinci Resolve 18", "CapCut 3.2", "FFmpeg 6.0",
                "iMovie 10.3", "Final Cut Pro X", "Filmora 13", "VLC media player"]
    handler_names = ["VideoHandler", "MainHandler", "ISO Media", "Apple Video Media Handler",
                     "Core Media Video", "GPAC ISO Video Handler", "Mainconcept Video Media Handler"]

    random_title = ''.join(random.choices(string.ascii_letters + string.digits + ' _-', k=random.randint(8, 32)))
    random_comment = ''.join(random.choices(string.ascii_letters + string.digits + ' .,!', k=random.randint(10, 48)))
    random_encoder = random.choice(encoders)
    random_handler = random.choice(handler_names)

    # Date de création aléatoire (entre -30 jours et maintenant)
    random_days = random.uniform(0, 30)
    random_creation = (datetime.now() - timedelta(days=random_days)).isoformat() + "Z"

    # UUID unique pour chaque fichier
    random_uuid = str(uuid.uuid4())

    # Tracer toutes les modifications appliquées
    modifications = {
        "speed": round(speed, 3),
        "hue_shift": hue_shift,
        "saturation": round(saturation, 2),
        "brightness": round(brightness, 3),
        "crop_percent": round(crop_pct * 100, 1),
        "hflip": do_hflip,
        "crf": crf,
        "metadata_randomized": True
    }

    cmd = ["ffmpeg", "-y", "-i", input_path, "-vf", video_filter]

    if audio_filter:
        cmd.extend(["-af", audio_filter])

    cmd.extend(["-c:v", "libx264", "-crf", str(crf), "-preset", "ultrafast", "-c:a", "aac", "-b:a", "128k"])

    # Métadonnées aléatoires (max variées entre chaque variation)
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
    """Génère un nom de dossier avec date et heure en français"""
    now = datetime.now()
    
    # Mois en français
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
    """Génère plusieurs variations uniques avec noms V01, V02, etc."""
    
    # Créer dossier daté
    folder_name = get_dated_folder_name()
    dated_dir = os.path.join(output_dir, folder_name)
    os.makedirs(dated_dir, exist_ok=True)
    
    results = []
    
    for i in range(count):
        # Nom simple: V01.mp4, V02.mp4, etc.
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
