"""
Video Processor - Platform-specific resizing and processing
"""
import subprocess
import os
from pathlib import Path

from uniquifier import FFMPEG_BIN, FFPROBE_BIN

PLATFORM_SPECS = {
    "tiktok": {"width": 1080, "height": 1920, "max_duration": 180},
    "instagram_reels": {"width": 1080, "height": 1920, "max_duration": 90},
    "youtube_shorts": {"width": 1080, "height": 1920, "max_duration": 60}
}

class VideoProcessor:
    def __init__(self):
        self.specs = PLATFORM_SPECS
    
    def resize_for_platform(self, input_path, output_path, platform):
        """Redimensionne une vidéo pour une plateforme spécifique"""
        spec = self.specs.get(platform, self.specs["tiktok"])
        w, h = spec["width"], spec["height"]
        
        cmd = [
            FFMPEG_BIN, "-y", "-i", input_path,
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-crf", "20", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k",
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def smart_crop(self, input_path, output_path, target_ratio="9:16"):
        """Crop intelligent pour format vertical"""
        cmd = [
            FFMPEG_BIN, "-y", "-i", input_path,
            "-vf", "crop=ih*9/16:ih",
            "-c:v", "libx264", "-crf", "20",
            "-c:a", "copy",
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        except Exception:
            return False
    
    def split_into_clips(self, input_path, output_dir, clip_duration=30):
        """Découpe une vidéo en clips courts"""
        os.makedirs(output_dir, exist_ok=True)
        base_name = Path(input_path).stem
        
        # Get duration
        if not FFPROBE_BIN:
            return []
        probe_cmd = [
            FFPROBE_BIN, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", input_path
        ]
        
        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip())
        except Exception:
            return []
        
        clips = []
        start = 0
        clip_num = 1
        
        while start < duration:
            output_path = os.path.join(output_dir, f"{base_name}_clip{clip_num:02d}.mp4")
            
            cmd = [
                FFMPEG_BIN, "-y", "-i", input_path,
                "-ss", str(start), "-t", str(clip_duration),
                "-c:v", "libx264", "-crf", "20",
                "-c:a", "aac",
                output_path
            ]
            
            subprocess.run(cmd, capture_output=True, timeout=120)
            clips.append(output_path)
            
            start += clip_duration
            clip_num += 1
        
        return clips
