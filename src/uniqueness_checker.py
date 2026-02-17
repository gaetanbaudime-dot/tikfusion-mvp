"""
Uniqueness Checker - Multi-platform duplicate detection
"""
import os
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import subprocess

from uniquifier import FFMPEG_BIN, FFPROBE_BIN

@dataclass
class PlatformScore:
    platform: str
    uniqueness_score: int
    risk_level: str
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

@dataclass 
class UniquenessReport:
    video_path: str
    video_hash: str
    overall_score: int
    tiktok: PlatformScore
    instagram: PlatformScore
    youtube: PlatformScore
    duplicate_found: bool = False
    similar_videos: List[Dict] = field(default_factory=list)

class UniquenessChecker:
    def __init__(self, library_path="video_library"):
        self.library_path = library_path
        self.hashes_file = os.path.join(library_path, "hashes.json")
        self._ensure_library()
    
    def _ensure_library(self):
        os.makedirs(self.library_path, exist_ok=True)
        if not os.path.exists(self.hashes_file):
            with open(self.hashes_file, 'w') as f:
                json.dump({}, f)
    
    def _compute_video_hash(self, video_path):
        """Compute perceptual hash using frame sampling"""
        try:
            from PIL import Image
            import imagehash
            import tempfile
            
            # Extract frames
            with tempfile.TemporaryDirectory() as tmpdir:
                cmd = [
                    FFMPEG_BIN, "-i", video_path,
                    "-vf", "fps=1,scale=64:64",
                    "-frames:v", "8",
                    f"{tmpdir}/frame_%02d.jpg"
                ]
                subprocess.run(cmd, capture_output=True, timeout=60)
                
                # Hash frames
                hashes = []
                for i in range(1, 9):
                    frame_path = f"{tmpdir}/frame_{i:02d}.jpg"
                    if os.path.exists(frame_path):
                        img = Image.open(frame_path)
                        h = imagehash.phash(img)
                        hashes.append(str(h))
                
                return "_".join(hashes) if hashes else self._file_hash(video_path)
        except Exception as e:
            return self._file_hash(video_path)
    
    def _file_hash(self, path):
        """Fallback: simple file hash"""
        h = hashlib.md5()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    
    def _get_video_info(self, video_path):
        """Get video metadata"""
        if not FFPROBE_BIN:
            return {}
        cmd = [
            FFPROBE_BIN, "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", video_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return json.loads(result.stdout)
        except Exception:
            return {}
    
    def _evaluate_tiktok(self, video_path, video_hash, info):
        """TikTok: strictest detection (deep learning + perceptual hash)"""
        score = 100
        issues = []
        recommendations = []
        
        # Check duration
        try:
            duration = float(info.get('format', {}).get('duration', 0))
            if duration > 180:
                score -= 10
                issues.append("Vidéo trop longue (>3min)")
                recommendations.append("Découper en clips <3min")
        except Exception:
            pass
        
        # Check for duplicates in library
        dup_score = self._check_library_duplicates(video_hash)
        if dup_score > 90:
            score -= 40
            issues.append("Hash très similaire détecté dans la bibliothèque")
            recommendations.append("Appliquer plus de modifications (intensité high)")
        elif dup_score > 70:
            score -= 20
            issues.append("Similarité modérée avec vidéos existantes")
            recommendations.append("Ajouter des effets visuels supplémentaires")
        
        # TikTok specific checks
        streams = info.get('streams', [])
        for stream in streams:
            if stream.get('codec_type') == 'video':
                # Check resolution
                w = stream.get('width', 0)
                h = stream.get('height', 0)
                if w != 1080 or h != 1920:
                    score -= 5
                    issues.append(f"Résolution non optimale: {w}x{h}")
                    recommendations.append("Redimensionner en 1080x1920")
        
        # Base uniqueness penalty
        score -= 10  # TikTok is strict
        
        risk = self._get_risk_level(score)
        return PlatformScore("tiktok", max(0, score), risk, issues, recommendations)
    
    def _evaluate_instagram(self, video_path, video_hash, info):
        """Instagram: moderate detection (watermark + content matching)"""
        score = 100
        issues = []
        recommendations = []
        
        # Check duration for Reels
        try:
            duration = float(info.get('format', {}).get('duration', 0))
            if duration > 90:
                score -= 10
                issues.append("Vidéo longue pour Reels (>90s)")
                recommendations.append("Idéal: 15-60 secondes")
        except Exception:
            pass
        
        # Check duplicates
        dup_score = self._check_library_duplicates(video_hash)
        if dup_score > 85:
            score -= 30
            issues.append("Contenu très similaire détecté")
            recommendations.append("Modifier la composition visuelle")
        elif dup_score > 60:
            score -= 15
            issues.append("Similarité modérée")
        
        # Instagram is more lenient
        risk = self._get_risk_level(score)
        return PlatformScore("instagram", max(0, score), risk, issues, recommendations)
    
    def _evaluate_youtube(self, video_path, video_hash, info):
        """YouTube: Content ID focus (audio fingerprinting)"""
        score = 100
        issues = []
        recommendations = []
        
        # Check duration for Shorts
        try:
            duration = float(info.get('format', {}).get('duration', 0))
            if duration > 60:
                score -= 5
                issues.append("Dépasse 60s (limite Shorts)")
                recommendations.append("Couper à <60s pour Shorts")
        except Exception:
            pass
        
        # Check for audio (Content ID risk)
        streams = info.get('streams', [])
        has_audio = any(s.get('codec_type') == 'audio' for s in streams)
        if has_audio:
            score -= 15
            issues.append("Audio présent (risque Content ID)")
            recommendations.append("Utiliser musique libre de droits ou modifier le pitch audio")
        
        # Check duplicates
        dup_score = self._check_library_duplicates(video_hash)
        if dup_score > 80:
            score -= 25
            issues.append("Vidéo similaire dans la bibliothèque")
            recommendations.append("Appliquer des modifications visuelles")
        
        risk = self._get_risk_level(score)
        return PlatformScore("youtube", max(0, score), risk, issues, recommendations)
    
    def _check_library_duplicates(self, video_hash):
        """Check similarity with existing videos in library"""
        try:
            with open(self.hashes_file, 'r') as f:
                library = json.load(f)
            
            if not library:
                return 0
            
            max_similarity = 0
            hash_parts = video_hash.split('_')
            
            for stored_hash in library.keys():
                stored_parts = stored_hash.split('_')
                
                # Compare hash parts
                if len(hash_parts) == len(stored_parts):
                    matches = sum(1 for a, b in zip(hash_parts, stored_parts) if a == b)
                    similarity = (matches / len(hash_parts)) * 100
                    max_similarity = max(max_similarity, similarity)
                elif video_hash == stored_hash:
                    max_similarity = 100
            
            return max_similarity
        except Exception:
            return 0
    
    def _get_risk_level(self, score):
        if score >= 80:
            return "low"
        elif score >= 60:
            return "medium"
        elif score >= 40:
            return "high"
        return "critical"
    
    def check_uniqueness(self, video_path, add_to_library=False):
        """Main check function - returns UniquenessReport"""
        video_hash = self._compute_video_hash(video_path)
        info = self._get_video_info(video_path)
        
        # Evaluate per platform
        tiktok = self._evaluate_tiktok(video_path, video_hash, info)
        instagram = self._evaluate_instagram(video_path, video_hash, info)
        youtube = self._evaluate_youtube(video_path, video_hash, info)
        
        # Overall score (weighted average - TikTok strictest)
        overall = int((tiktok.uniqueness_score * 0.4 + 
                      instagram.uniqueness_score * 0.3 + 
                      youtube.uniqueness_score * 0.3))
        
        # Check for duplicates
        dup_score = self._check_library_duplicates(video_hash)
        duplicate_found = dup_score > 80
        
        # Add to library if requested
        if add_to_library:
            self._add_to_library(video_path, video_hash, overall, tiktok, instagram, youtube)
        
        return UniquenessReport(
            video_path=video_path,
            video_hash=video_hash,
            overall_score=overall,
            tiktok=tiktok,
            instagram=instagram,
            youtube=youtube,
            duplicate_found=duplicate_found
        )
    
    def _add_to_library(self, video_path, video_hash, overall, tiktok, instagram, youtube):
        """Add video to library"""
        try:
            with open(self.hashes_file, 'r') as f:
                library = json.load(f)
            
            library[video_hash] = {
                "path": video_path,
                "scores": {
                    "overall": overall,
                    "tiktok": tiktok.uniqueness_score,
                    "instagram": instagram.uniqueness_score,
                    "youtube": youtube.uniqueness_score
                }
            }
            
            with open(self.hashes_file, 'w') as f:
                json.dump(library, f, indent=2)
        except Exception:
            pass
    
    def compare_videos(self, video1_path, video2_path):
        """Compare two videos for similarity"""
        hash1 = self._compute_video_hash(video1_path)
        hash2 = self._compute_video_hash(video2_path)
        
        parts1 = hash1.split('_')
        parts2 = hash2.split('_')
        
        if len(parts1) == len(parts2) and len(parts1) > 1:
            matches = sum(1 for a, b in zip(parts1, parts2) if a == b)
            similarity = (matches / len(parts1)) * 100
        elif hash1 == hash2:
            similarity = 100
        else:
            similarity = 0
        
        verdict = "✅ Suffisamment différentes" if similarity < 70 else "⚠️ Trop similaires"
        
        return {
            "similarity_percent": round(similarity, 1),
            "verdict": verdict,
            "hash1": hash1,
            "hash2": hash2
        }
