"""
TikFusion v5 — Professional video uniquifier
Import URL | Single | Bulk | Ferme | Statistiques | Configuration
"""
import streamlit as st
import os
import sys
import json
import random
import subprocess
import shutil
import tempfile
import base64
import zipfile
import io
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

st.set_page_config(page_title="TikFusion x LTP", page_icon="assets/favicon.svg", layout="wide", initial_sidebar_state="collapsed")

# ============ CSS ============
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none; }
    * { font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif; }

    /* Header */
    .header-bar {
        display: flex; align-items: center; justify-content: center; gap: 16px;
        padding: 12px 0 8px 0; border-bottom: 1px solid #2C2C2E; margin-bottom: 16px;
    }
    .header-logo {
        background: #F5F5F7; color: #000; font-weight: 800; font-size: 1.3rem;
        padding: 6px 14px; border-radius: 8px; letter-spacing: 2px;
    }
    .header-title { font-size: 2rem; font-weight: 700; color: #F5F5F7; letter-spacing: -0.5px; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 0; background: #1C1C1E; border-radius: 12px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 8px 20px; font-weight: 500; color: #86868B !important; }
    .stTabs [aria-selected="true"] { background: #007AFF !important; color: #FFF !important; }
    .stTabs [data-baseweb="tab"] p, .stTabs [data-baseweb="tab"] span { color: inherit !important; }

    /* Buttons */
    .stButton > button[kind="primary"] { background: #007AFF; border: none; border-radius: 10px; font-weight: 600; }
    .stButton > button[kind="primary"]:hover { background: #0056CC; }
    .stDownloadButton > button { background: #2C2C2E; border: 1px solid #3A3A3C; border-radius: 8px; font-size: 0.75rem; }

    /* Compact video in upload panel */
    .compact-video video { max-height: 180px !important; border-radius: 10px; }

    /* Tags */
    .tag-sm {
        display: inline-block; padding: 2px 5px; border-radius: 4px;
        font-size: 0.62rem; font-weight: 500; margin: 1px;
    }
    .tag-mirror { background: #FF453A; color: white; }
    .tag-speed { background: #1C1C1E; color: #64D2FF; border: 1px solid #3A3A3C; }
    .tag-hue { background: #1C1C1E; color: #FF9F0A; border: 1px solid #3A3A3C; }
    .tag-crop { background: #1C1C1E; color: #30D158; border: 1px solid #3A3A3C; }
    .tag-zoom { background: #1C1C1E; color: #FFD60A; border: 1px solid #3A3A3C; }
    .tag-noise { background: #1C1C1E; color: #FF6482; border: 1px solid #3A3A3C; }
    .tag-pitch { background: #1C1C1E; color: #5E5CE6; border: 1px solid #3A3A3C; }
    .tag-meta { background: #1C1C1E; color: #BF5AF2; border: 1px solid #3A3A3C; }

    /* Badges */
    .badge-safe { background: #30D158; color: white; padding: 3px 10px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    .badge-warning { background: #FF9F0A; color: white; padding: 3px 10px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    .badge-danger { background: #FF453A; color: white; padding: 3px 10px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }

    /* Result grid — reordered: # | Score | Modifications | Apercu */
    .rg-table { width: 100%; border-collapse: separate; border-spacing: 0 3px; }
    .rg-head td {
        padding: 4px 10px; font-size: 0.68rem; font-weight: 600; color: #48484A;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .rg-row td {
        background: #1C1C1E; padding: 5px 10px; vertical-align: middle;
    }
    .rg-row td:first-child { border-radius: 10px 0 0 10px; }
    .rg-row td:last-child { border-radius: 0 10px 10px 0; }
    .rg-row:hover td { background: #232325; }
    .rg-name { font-weight: 700; font-size: 0.85rem; color: #F5F5F7; white-space: nowrap; }
    .rg-tags { line-height: 1.8; display: inline-flex; flex-wrap: wrap; gap: 2px; max-width: 340px; }
    .rg-score { text-align: left; white-space: nowrap; }
    .rg-thumb { height: 110px; border-radius: 6px; object-fit: cover; }

    /* Summary bar */
    .summary-bar {
        background: #1C1C1E; border: 1px solid #2C2C2E; border-radius: 10px;
        padding: 8px 14px; margin: 6px 0; font-size: 0.78rem; color: #86868B;
    }

    /* Legend */
    .legend {
        background: #1C1C1E; border: 1px solid #2C2C2E; border-radius: 8px;
        padding: 5px 12px; font-size: 0.7rem; color: #86868B; margin-bottom: 8px;
    }

    /* Folder badge */
    .folder-badge {
        background: #1C1C1E; color: #64D2FF; padding: 5px 12px; border-radius: 8px;
        font-family: 'SF Mono', monospace; font-size: 0.78rem;
        border: 1px solid #2C2C2E; display: inline-block; margin-bottom: 6px;
    }

    /* Virality card */
    .vir-card { background: #1C1C1E; border: 1px solid #2C2C2E; border-radius: 14px; padding: 14px; margin: 6px 0; }
    .vir-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
    .vir-title { font-size: 0.95rem; font-weight: 600; color: #F5F5F7; }
    .vir-row { margin: 4px 0; }
    .vir-lbl { display: flex; justify-content: space-between; color: #86868B; font-size: 0.7rem; margin-bottom: 2px; }
    .vir-bar { background: #2C2C2E; border-radius: 3px; height: 4px; overflow: hidden; }
    .vir-fill { height: 100%; border-radius: 3px; }
    .vir-tips { margin-top: 8px; padding: 8px; background: #2C2C2E; border-radius: 8px; color: #FF9F0A; font-size: 0.68rem; }
    .vir-why { margin-top: 8px; padding: 8px; background: #0A2F1C; border: 1px solid #30D158; border-radius: 8px; color: #30D158; font-size: 0.7rem; }

    /* Engagement stat chips */
    .eng-chip {
        display: inline-block; background: #2C2C2E; border-radius: 8px;
        padding: 6px 12px; font-size: 0.78rem; color: #F5F5F7; font-weight: 500;
    }
    .eng-chips { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }

    /* Platform badges */
    .plat { display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 0.72rem; font-weight: 600; }
    .plat-tiktok { background: #1C1C1E; color: #FF004F; border: 1px solid #FF004F; }
    .plat-instagram { background: #1C1C1E; color: #E1306C; border: 1px solid #E1306C; }
    .plat-youtube { background: #1C1C1E; color: #FF0000; border: 1px solid #FF0000; }
    .plat-other { background: #1C1C1E; color: #86868B; border: 1px solid #3A3A3C; }

    /* Metrics */
    [data-testid="stMetric"] { background: #1C1C1E; border: 1px solid #2C2C2E; border-radius: 12px; padding: 10px; }

    /* Reduce vertical gap in result area */
    [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] { margin-bottom: -6px; }

    /* Tight download strip */
    .dl-strip { margin-top: 2px; }
    .dl-strip .stDownloadButton > button {
        padding: 4px 8px !important; font-size: 0.7rem !important;
        background: #1C1C1E !important; border: 1px solid #2C2C2E !important;
    }
    .dl-strip .stDownloadButton > button:hover { background: #2C2C2E !important; }

    /* Video preview grid */
    .preview-grid video { border-radius: 10px; max-height: 200px; }
    .preview-label { font-size: 0.72rem; color: #86868B; text-align: center; margin-top: 2px; }

    /* Expander */
    .streamlit-expanderHeader { background: #1C1C1E; border-radius: 10px; font-size: 0.85rem; }

    /* Info card for Config */
    .info-card {
        background: #1C1C1E; border: 1px solid #2C2C2E; border-radius: 14px;
        padding: 16px; margin: 10px 0;
    }
    .info-card h4 { color: #F5F5F7; margin: 0 0 8px 0; }
    .info-card p { color: #86868B; font-size: 0.82rem; margin: 4px 0; }
    .info-card .highlight { color: #F5F5F7; font-weight: 600; }
    .info-card .step { color: #86868B; font-size: 0.78rem; line-height: 1.8; }

    /* Farm progress */
    .farm-metric {
        background: #1C1C1E; border: 1px solid #2C2C2E; border-radius: 12px;
        padding: 12px; text-align: center;
    }
    .farm-metric .value { font-size: 1.4rem; font-weight: 700; color: #F5F5F7; }
    .farm-metric .label { font-size: 0.7rem; color: #86868B; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)


# ============ CORE FUNCTIONS ============

def estimate_uniqueness(modifications):
    score = 0
    score += min(modifications.get("noise", 0) * 3, 18)
    score += min((modifications.get("zoom", 1.0) - 1.0) * 350, 14)
    score += min(abs(modifications.get("gamma", 1.0) - 1.0) * 200, 5)
    score += min(abs(modifications.get("hue_shift", 0)) * 0.15, 2)
    if modifications.get("hflip", False): score += 12
    score += min(modifications.get("crop_percent", 0) * 2, 4)
    score += min(abs(modifications.get("speed", 1.0) - 1.0) * 40, 3)
    score += min(abs(modifications.get("pitch_semitones", 0)) * 35, 20)
    score += min(abs(modifications.get("fps", 30) - 30) * 50, 5)
    score += 3  # volume
    if modifications.get("metadata_randomized", False): score += 5
    score += 8  # re-encoding
    return {'uniqueness': min(round(score), 100)}


def get_dated_folder_name():
    now = datetime.now()
    m = {1:"janvier",2:"fevrier",3:"mars",4:"avril",5:"mai",6:"juin",
         7:"juillet",8:"aout",9:"septembre",10:"octobre",11:"novembre",12:"decembre"}
    return f"{now.day} {m[now.month]} {now.strftime('%Hh%M')}"


def format_tags(mods):
    t = []
    if mods.get("hflip"): t.append('<span class="tag-sm tag-mirror">🪞 Miroir</span>')
    s = mods.get("speed", 1.0)
    if abs(s-1) > .005: t.append(f'<span class="tag-sm tag-speed">🔄 x{s:.2f}</span>')
    h = mods.get("hue_shift", 0)
    if abs(h) > 0: t.append(f'<span class="tag-sm tag-hue">🎨 {h:+d}°</span>')
    c = mods.get("crop_percent", 0)
    if c > .1: t.append(f'<span class="tag-sm tag-crop">✂️ {c:.1f}%</span>')
    z = mods.get("zoom", 1.0)
    if z > 1.005: t.append(f'<span class="tag-sm tag-zoom">🔍 {(z-1)*100:.1f}%</span>')
    n = mods.get("noise", 0)
    if n > 0: t.append(f'<span class="tag-sm tag-noise">📡 N{n:.0f}</span>')
    p = mods.get("pitch_semitones", 0)
    if abs(p) > .05: t.append(f'<span class="tag-sm tag-pitch">🎵 {p:+.1f}st</span>')
    if mods.get("metadata_randomized"): t.append('<span class="tag-sm tag-meta">🏷️ Meta</span>')
    return " ".join(t) if t else '<span style="color:#48484A;font-size:.7rem">—</span>'


def get_badge(score):
    """Badges calibres Instagram — la plateforme la plus stricte"""
    if score >= 60:
        return 'badge-safe', 'Safe Instagram'
    if score >= 30:
        return 'badge-warning', 'Safe TikTok'
    return 'badge-danger', 'Risque'


def extract_thumbnail(video_path):
    thumb = video_path + ".thumb.jpg"
    if os.path.exists(thumb): return thumb
    try:
        subprocess.run(["ffmpeg","-y","-i",video_path,"-vf","thumbnail,scale=160:-1",
                        "-frames:v","1","-q:v","5",thumb], capture_output=True, timeout=10)
        return thumb if os.path.exists(thumb) else None
    except Exception:
        return None


def thumb_b64(path):
    """Get thumbnail as base64 string for HTML embedding"""
    thumb = extract_thumbnail(path) if not path.endswith('.thumb.jpg') else path
    if thumb and os.path.exists(thumb):
        with open(thumb, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None


# ============ URL DOWNLOAD ============

def detect_platform(url):
    if not url: return None
    u = url.lower()
    if "tiktok.com" in u: return "tiktok"
    if "instagram.com" in u: return "instagram"
    if "youtube.com" in u or "youtu.be" in u: return "youtube"
    return "other"


def download_from_url(url):
    try:
        tmpdir = tempfile.mkdtemp()
        cmd = [sys.executable, "-m", "yt_dlp", "--no-playlist",
               "--merge-output-format", "mp4", "-o", os.path.join(tmpdir, "video.%(ext)s"), url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

        if result.returncode != 0:
            shutil.rmtree(tmpdir, ignore_errors=True)
            err = result.stderr.strip().split('\n')[-1] if result.stderr else "Erreur inconnue"
            return None, err[:300]

        files = [f for f in os.listdir(tmpdir) if os.path.isfile(os.path.join(tmpdir, f))]
        if not files:
            shutil.rmtree(tmpdir, ignore_errors=True)
            return None, "Aucun fichier telecharge"

        src = os.path.join(tmpdir, files[0])
        final = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        final.close()

        if src.endswith('.mp4'):
            shutil.move(src, final.name)
        else:
            r = subprocess.run(["ffmpeg","-y","-i",src,"-c:v","libx264","-c:a","aac",
                                "-preset","ultrafast",final.name], capture_output=True, timeout=120)
            if r.returncode != 0:
                shutil.rmtree(tmpdir, ignore_errors=True)
                return None, "Conversion MP4 echouee"

        shutil.rmtree(tmpdir, ignore_errors=True)
        if os.path.exists(final.name) and os.path.getsize(final.name) > 0:
            return final.name, None
        return None, "Fichier vide"
    except subprocess.TimeoutExpired:
        return None, "Timeout — video trop longue"
    except Exception as e:
        return None, str(e)


# ============ ENGAGEMENT SCRAPING (Import URL only) ============

def scrape_engagement_stats(url):
    """Scrape les stats d'engagement depuis l'URL source via yt-dlp --dump-json"""
    try:
        cmd = [sys.executable, "-m", "yt_dlp", "--dump-json", "--no-download", url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return None, "Impossible de scraper les stats"

        data = json.loads(result.stdout)

        return {
            'views': data.get('view_count', 0) or 0,
            'likes': data.get('like_count', 0) or 0,
            'comments': data.get('comment_count', 0) or 0,
            'shares': data.get('repost_count', 0) or data.get('share_count', 0) or 0,
            'title': data.get('title', '') or '',
            'uploader': data.get('uploader', '') or data.get('channel', '') or '',
            'duration': data.get('duration', 0) or 0,
            'description': data.get('description', '') or '',
        }, None
    except subprocess.TimeoutExpired:
        return None, "Timeout scraping"
    except Exception as e:
        return None, str(e)


def calculate_virality_score(stats):
    """Score de viralite base sur l'engagement reel scrape"""
    views = max(stats['views'], 1)
    likes = stats['likes']
    comments = stats['comments']
    shares = stats['shares']

    engagement_rate = (likes + comments + shares) / views
    like_ratio = likes / views
    comment_ratio = comments / views

    score = 0
    breakdown = []
    tips = []
    why = []

    # 1. Vues (30 pts)
    if views >= 1_000_000:
        pts = 30; why.append(f"{views:,} vues — contenu massif, viralite confirmee")
    elif views >= 100_000:
        pts = 25; why.append(f"{views:,} vues — forte portee organique")
    elif views >= 10_000:
        pts = 18
    elif views >= 1_000:
        pts = 10
    else:
        pts = 3; tips.append("Portee faible (<1K vues) — tester d'autres hooks")
    breakdown.append(("👁 Vues", f"{views:,}", pts, 30))
    score += pts

    # 2. Engagement rate (30 pts)
    if engagement_rate >= 0.10:
        pts = 30; why.append(f"Engagement {engagement_rate*100:.1f}% — exceptionnel (>10%)")
    elif engagement_rate >= 0.05:
        pts = 24; why.append(f"Engagement {engagement_rate*100:.1f}% — tres bon (>5%)")
    elif engagement_rate >= 0.02:
        pts = 16
    elif engagement_rate >= 0.01:
        pts = 8
    else:
        pts = 2; tips.append("Engagement rate faible — ameliorer le hook d'accroche")
    breakdown.append(("🔥 Engagement", f"{engagement_rate*100:.2f}%", pts, 30))
    score += pts

    # 3. Like ratio (20 pts)
    if like_ratio >= 0.08:
        pts = 20; why.append(f"Like ratio {like_ratio*100:.1f}% — le contenu plait beaucoup")
    elif like_ratio >= 0.04:
        pts = 15
    elif like_ratio >= 0.02:
        pts = 10
    else:
        pts = 4
    breakdown.append(("❤️ Likes", f"{likes:,} ({like_ratio*100:.1f}%)", pts, 20))
    score += pts

    # 4. Comment ratio (20 pts) — signal fort de viralite
    if comment_ratio >= 0.02:
        pts = 20; why.append(f"Comment ratio {comment_ratio*100:.2f}% — declenche la conversation")
    elif comment_ratio >= 0.005:
        pts = 14
    elif comment_ratio >= 0.001:
        pts = 8
    else:
        pts = 2; tips.append("Peu de commentaires — ajouter un CTA pour inciter le debat")
    breakdown.append(("💬 Commentaires", f"{comments:,} ({comment_ratio*100:.2f}%)", pts, 20))
    score += pts

    return {
        'score': min(score, 100),
        'breakdown': breakdown,
        'tips': tips,
        'why': why,
        'stats': stats,
        'engagement_rate': engagement_rate,
    }


def render_virality(analysis):
    """Render le score de viralite base sur l'engagement"""
    s = analysis['score']
    badge_class, badge_label = get_badge(s)
    stats = analysis.get('stats', {})

    # Chips de stats brutes
    chips_html = '<div class="eng-chips">'
    if stats.get('views', 0) > 0:
        chips_html += f'<span class="eng-chip">👁 {stats["views"]:,} vues</span>'
    if stats.get('likes', 0) > 0:
        chips_html += f'<span class="eng-chip">❤️ {stats["likes"]:,} likes</span>'
    if stats.get('comments', 0) > 0:
        chips_html += f'<span class="eng-chip">💬 {stats["comments"]:,} commentaires</span>'
    if stats.get('shares', 0) > 0:
        chips_html += f'<span class="eng-chip">🔄 {stats["shares"]:,} partages</span>'
    chips_html += '</div>'

    # Uploader info
    uploader = stats.get('uploader', '')
    uploader_html = f'<div style="color:#86868B;font-size:0.72rem;margin-bottom:8px">👤 {uploader}</div>' if uploader else ''

    # Breakdown bars
    rows = ""
    for label, desc, pts, mx in analysis['breakdown']:
        pct = (pts/mx*100) if mx else 0
        col = "#30D158" if pct >= 70 else "#FF9F0A" if pct >= 40 else "#FF453A"
        rows += f"""<div class="vir-row"><div class="vir-lbl"><span>{label} — {desc}</span><span style="color:#F5F5F7;font-weight:500">{pts}/{mx}</span></div>
        <div class="vir-bar"><div class="vir-fill" style="background:{col};width:{pct}%"></div></div></div>"""

    tips = ""
    if analysis['tips']:
        items = "".join(f"<div>💡 {t}</div>" for t in analysis['tips'])
        tips = f'<div class="vir-tips">{items}</div>'

    why = ""
    if analysis['why']:
        items = "".join(f"<div>✅ {w}</div>" for w in analysis['why'])
        why = f'<div class="vir-why"><div style="font-weight:600;margin-bottom:4px">Pourquoi ca marche :</div>{items}</div>'

    return f"""<div class="vir-card"><div class="vir-head">
        <span class="vir-title">🔥 Score de Viralite</span>
        <span class="{badge_class}" style="font-size:1rem;padding:5px 14px">{s}/100</span>
    </div>{uploader_html}{chips_html}{rows}{why}{tips}</div>"""


# ============ CAPTION OCR + GENERATION ============

def generate_captions_from_ocr(video_path):
    """Extraire le texte via OCR et generer 10 variantes de captions (texte SUR la video)"""
    original_texts = []
    try:
        from caption_ocr import extract_text_from_video
        original_texts = extract_text_from_video(video_path, num_frames=8)
    except Exception:
        pass

    if original_texts:
        # Extraire les mots-cles du texte OCR
        words = []
        for t in original_texts:
            for w in t.split():
                w_clean = w.strip('.,!?;:()[]"\'')
                if len(w_clean) > 3 and w_clean.isalpha():
                    words.append(w_clean)
        topic = " ".join(words[:4]) if words else "ca"

        templates = [
            f"Personne ne parle de {topic} mais...",
            f"La verite sur {topic}",
            f"{topic} — ce que tu rates",
            f"POV: tu decouvres {topic}",
            f"Stop scroll — {topic}",
            f"Le secret de {topic}",
            f"{topic} change tout",
            f"Fais ca avec {topic}",
            f"{topic} avant qu'il soit trop tard",
            f"Tu ne savais pas ca sur {topic}",
        ]
        return templates, original_texts
    else:
        generic = [
            "Regarde ca de plus pres...",
            "Ce detail change tout",
            "Personne ne remarque ca",
            "POV: tu vois ca pour la premiere fois",
            "Attends la fin...",
            "Le moment ou tout bascule",
            "Ce que personne ne te dit",
            "Stop le scroll — regarde",
            "3 secondes qui changent tout",
            "Tu passes a cote si tu scrolles",
        ]
        return generic, []


def generate_descriptions(duration=0):
    """Generer 10 variantes de descriptions (texte SOUS la video) — hooks + CTA + hashtags"""
    hooks_curiosite = [
        "Personne ne parle de ca mais...",
        "Ce que personne ne te dit sur...",
        "La verite que tout le monde ignore",
        "Tu ne devineras jamais ce qui se passe",
        "Le secret que les pros cachent",
    ]
    hooks_valeur = [
        "3 astuces que j'utilise tous les jours",
        "Fais ca et remercie-moi plus tard",
        "La methode qui a tout change pour moi",
        "L'astuce que j'aurais aime connaitre avant",
        "Voici comment faire en 30 secondes",
    ]
    hooks_emotion = [
        "Ca m'a laisse sans voix...",
        "Quand tu realises que...",
        "POV: tu decouvres ca pour la premiere fois",
        "Avant vs Apres — la difference est folle",
        "Le moment ou tout a bascule",
    ]
    hooks_urgence = [
        "Sauvegarde avant que ca disparaisse",
        "Stop le scroll — regarde ca",
        "Si tu vois cette video c'est un signe",
        "Ne rate pas la fin surtout",
        "Tu passes a cote si tu scrolles",
    ]
    ctas = [
        "Follow pour plus 🔥",
        "Like si tu veux la partie 2",
        "Commente 🔥 si ca t'a aide",
        "Enregistre pour plus tard 📌",
        "Partage a quelqu'un qui en a besoin",
        "Abonne-toi pour la suite",
        "Dis-moi en commentaire ce que t'en penses",
    ]
    tags = [
        "#fyp #pourtoi #viral #trending",
        "#foryou #astuce #hack #tips",
        "#trend #viral #mustsee #pourtoi",
        "#fyp #trending #mindblown #viral2026",
        "#reels #explore #trending #content",
    ]

    pool = (random.sample(hooks_curiosite, 2) + random.sample(hooks_valeur, 3) +
            random.sample(hooks_emotion, 2) + random.sample(hooks_urgence, 3))
    random.shuffle(pool)

    variants = []
    for i in range(10):
        hook = pool[i]
        cta = random.choice(ctas)
        tag = random.choice(tags)
        if duration and duration <= 15:
            v = f"{hook}\n\n{cta}\n\n{tag}"
        elif duration and duration <= 45:
            v = f"{hook}\n\n💡 Regarde jusqu'a la fin\n\n{cta}\n\n{tag}"
        else:
            v = f"{hook}\n\n⬇️ Tout est dans la video\n\n{cta}\n\n{tag}"
        variants.append(v)
    return variants


# ============ GENERATION ENGINE ============

def run_generation(input_path, num_vars, output_dir, intensity, enabled_mods, progress_bar, status_el):
    from uniquifier import uniquify_video_ffmpeg
    folder = get_dated_folder_name()
    out_dir = os.path.join(output_dir, folder)
    os.makedirs(out_dir, exist_ok=True)

    results = []
    for i in range(num_vars):
        status_el.text(f"⏳ V{i+1:02d}/{num_vars}...")
        out = os.path.join(out_dir, f"V{i+1:02d}.mp4")
        r = uniquify_video_ffmpeg(input_path, out, intensity, enabled_mods)
        if r["success"]:
            mods = r.get("modifications", {})
            a = estimate_uniqueness(mods)
            a['name'] = Path(out).stem
            a['modifications'] = mods
            a['output_path'] = out
            a['thumbnail'] = extract_thumbnail(out)
            results.append(a)
        progress_bar.progress((i+1) / num_vars)
    return results, folder


# ============ RESULTS RENDERER ============

def build_grid_html(analyses):
    """Construire le tableau HTML — colonnes: # | Score | Modifications | Apercu"""
    grid = '<table class="rg-table"><tr class="rg-head"><td style="width:36px">#</td><td style="width:56px">Score</td><td>Modifications</td><td style="width:120px">Apercu</td></tr>'

    for a in analyses:
        u = a['uniqueness']
        badge_class, badge_label = get_badge(u)
        tags_html = format_tags(a.get('modifications', {}))

        # Thumbnail as base64
        thumb_img = '<span style="color:#48484A;font-size:.7rem">—</span>'
        t = a.get('thumbnail')
        if not t or not os.path.exists(t):
            t_path = a.get('output_path', '')
            if t_path and os.path.exists(t_path):
                t = extract_thumbnail(t_path)
        if t and os.path.exists(t):
            b64 = thumb_b64(t)
            if b64:
                thumb_img = f'<img src="data:image/jpeg;base64,{b64}" class="rg-thumb" />'

        grid += f"""<tr class="rg-row">
            <td><span class="rg-name">{a['name']}</span></td>
            <td class="rg-score"><span class="{badge_class}" style="font-size:0.72rem;padding:2px 8px">{u:.0f}%</span></td>
            <td><div class="rg-tags">{tags_html}</div></td>
            <td style="text-align:center">{thumb_img}</td>
        </tr>\n"""

    grid += '</table>'
    return grid


def render_results(analyses, folder, prefix, virality=None, captions_overlay=None, original_texts=None, descriptions=None):
    """Afficher les resultats de generation"""
    if not analyses:
        return

    # Top bar: folder + ZIP + summary
    avg = sum(a['uniqueness'] for a in analyses) / len(analyses)
    safe = sum(1 for a in analyses if a['uniqueness'] >= 60)

    top1, top2, top3 = st.columns([2, 1.5, 1.5])
    with top1:
        st.markdown(f"<div class='folder-badge'>📁 {folder}/</div>", unsafe_allow_html=True)
    with top2:
        st.markdown(f"""<div style="background:#1C1C1E;border:1px solid #2C2C2E;border-radius:8px;padding:6px 10px;
            font-size:0.78rem;color:#86868B;text-align:center">
            📊 Moy. <b style="color:#F5F5F7">{avg:.0f}%</b> &nbsp; ✅ <b style="color:#30D158">{safe}/{len(analyses)}</b> safe
        </div>""", unsafe_allow_html=True)
    with top3:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for a in analyses:
                p = a.get('output_path','')
                if p and os.path.exists(p):
                    zf.write(p, f"{a['name']}.mp4")
        buf.seek(0)
        st.download_button("📦 ZIP Tout", buf.getvalue(),
                           file_name=f"{folder}.zip", mime="application/zip",
                           key=f"zip_{prefix}", use_container_width=True)

    st.markdown("""<div class="legend">🟢 ≥60% = Safe Instagram (toutes plateformes) &nbsp;|&nbsp; 🟠 30-59% = Safe TikTok seulement &nbsp;|&nbsp; 🔴 <30% = Risque detection</div>""", unsafe_allow_html=True)

    # HTML table grid
    st.markdown(build_grid_html(analyses), unsafe_allow_html=True)

    # Download buttons strip (5 per line)
    max_per_row = 5
    for start in range(0, len(analyses), max_per_row):
        chunk = analyses[start:start+max_per_row]
        cols = st.columns(max_per_row)
        for i, a in enumerate(chunk):
            p = a.get('output_path','')
            if p and os.path.exists(p):
                with cols[i]:
                    with open(p, 'rb') as f:
                        st.download_button(f"⬇ {a['name']}", f.read(),
                                           file_name=f"{a['name']}.mp4", mime="video/mp4",
                                           key=f"dl_{prefix}_{start}_{i}", use_container_width=True)

    # Video preview gallery — visible, 3 per row
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("##### 🎬 Aperçus — verifier les modifications")
    preview_per_row = 3
    for start in range(0, len(analyses), preview_per_row):
        chunk = analyses[start:start+preview_per_row]
        pcols = st.columns(preview_per_row)
        for i, a in enumerate(chunk):
            p = a.get('output_path','')
            if p and os.path.exists(p):
                with pcols[i]:
                    st.video(p)
                    u = a['uniqueness']
                    badge_class, _ = get_badge(u)
                    st.markdown(f'<div style="text-align:center;margin-top:-6px"><span class="rg-name">{a["name"]}</span> &nbsp; <span class="{badge_class}" style="font-size:.72rem;padding:2px 8px">{u:.0f}%</span></div>', unsafe_allow_html=True)

    # Virality (Import URL only)
    if virality:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        with st.expander("🔥 Analyse de Viralite — Engagement reel", expanded=False):
            st.markdown(render_virality(virality), unsafe_allow_html=True)

    # Captions (texte SUR la video) — OCR-based
    if captions_overlay:
        with st.expander("🎬 10 Captions (texte sur la video)", expanded=False):
            if original_texts:
                combined = " | ".join(original_texts[:3])
                st.markdown(f'<div style="background:#2C2C2E;border-radius:8px;padding:8px;margin-bottom:8px;font-size:0.78rem;color:#86868B"><b style="color:#F5F5F7">Texte original detecte :</b> {combined}</div>', unsafe_allow_html=True)
            cap_cols = st.columns(2)
            for i, cap in enumerate(captions_overlay):
                with cap_cols[i % 2]:
                    st.code(cap, language=None)

    # Descriptions (texte SOUS la video)
    if descriptions:
        with st.expander("📝 10 Descriptions (texte sous la video)", expanded=False):
            desc_cols = st.columns(2)
            for i, desc in enumerate(descriptions):
                with desc_cols[i % 2]:
                    st.code(desc, language=None)


# ============ MAIN ============

def main():
    st.markdown("""<div class="header-bar">
        <span class="header-logo">LTP</span>
        <span class="header-title">TikFusion</span>
    </div>""", unsafe_allow_html=True)

    tab_url, tab_single, tab_bulk, tab_farm, tab_stats, tab_config = st.tabs([
        "🔗 Import", "📤 Single", "📦 Bulk", "🏭 Ferme",
        "📊 Statistiques", "⚙️ Configuration"
    ])

    # ===== CONFIGURATION (first for variables) =====
    with tab_config:
        st.markdown("### ⚙️ Configuration")
        c1, c2 = st.columns(2)
        with c1: output_dir = st.text_input("📁 Dossier de sortie", value="outputs", key="cfg_output")
        with c2: intensity = st.select_slider("🎚️ Intensite", options=["low","medium","high"], value="medium", key="cfg_intensity")

        st.markdown("---")
        st.markdown("### 🎛️ Modifications anti-detection")

        st.markdown("#### 👁️ Anti Hash Visuel — *~30-35% de la detection*")
        v1,v2 = st.columns(2)
        with v1:
            mod_noise = st.toggle("📡 Pixel Noise", value=True, key="mod_noise", help="Bruit invisible. Le plus efficace contre pHash.")
            mod_zoom = st.toggle("🔍 Zoom", value=True, key="mod_zoom", help="Zoom leger. Repositionne les pixels.")
        with v2:
            mod_gamma = st.toggle("🌗 Gamma", value=True, key="mod_gamma", help="Modifie la luminosite globale.")
            mod_hue = st.toggle("🎨 Couleur", value=True, key="mod_hue", help="Decale la teinte.")

        st.markdown("#### 🧠 Anti Deep Learning — *~25-30%*")
        s1,s2 = st.columns(2)
        with s1:
            mod_hflip = st.toggle("🪞 Miroir", value=True, key="mod_hflip", help="Inverse horizontalement.")
            mod_crop = st.toggle("✂️ Crop", value=True, key="mod_crop", help="Coupe les bords.")
        with s2:
            mod_speed = st.toggle("🔄 Vitesse", value=True, key="mod_speed", help="Change la vitesse.")

        st.markdown("#### 🔊 Anti Fingerprint Audio — *~20-25%*")
        a1,a2 = st.columns(2)
        with a1: mod_pitch = st.toggle("🎵 Pitch", value=True, key="mod_pitch", help="Decale la frequence audio.")
        with a2: mod_fps = st.toggle("🎞️ FPS", value=True, key="mod_fps", help="Change le framerate.")

        st.markdown("#### 🏷️ Metadata")
        mod_meta = st.toggle("🏷️ Metadata aleatoires", value=True, key="mod_meta", help="Randomise les metadonnees.")

        st.markdown("---")
        ps = 0; d = []
        if mod_noise: ps += 14; d.append("📡+14")
        if mod_zoom: ps += 12; d.append("🔍+12")
        if mod_gamma: ps += 4; d.append("🌗+4")
        if mod_hue: ps += 1; d.append("🎨+1")
        if mod_hflip: ps += 5; d.append("🪞+5")
        if mod_crop: ps += 2; d.append("✂️+2")
        if mod_speed: ps += 1; d.append("🔄+1")
        if mod_pitch: ps += 17; d.append("🎵+17")
        if mod_fps: ps += 3; d.append("🎞️+3")
        ps += 3; d.append("🔊+3")
        if mod_meta: ps += 5; d.append("🏷️+5")
        ps += 8; d.append("💾+8")
        ps = min(ps, 100)
        bc, bl = get_badge(ps)
        st.markdown(f"""<div style="background:#1C1C1E;border:1px solid #2C2C2E;border-radius:12px;padding:14px;margin:8px 0">
            <div style="display:flex;align-items:center;justify-content:space-between">
                <span style="font-size:1rem;font-weight:600;color:#F5F5F7">📊 Score estime moyen</span>
                <span class="{bc}" style="font-size:1.1rem;padding:5px 14px">{ps}% — {bl}</span>
            </div>
            <div style="color:#86868B;font-size:.72rem;margin-top:6px">{" · ".join(d)}</div>
        </div>""", unsafe_allow_html=True)

        # ===== INFO INSTAGRAM =====
        st.markdown("---")
        st.markdown("### 🛡️ Detection Instagram — Notre reference")
        st.markdown("""<div class="info-card">
            <h4>Pourquoi Instagram est notre reference</h4>
            <p>Instagram utilise l'algorithme de detection de doublons <span class="highlight">le plus strict</span>
            parmi toutes les plateformes. Si votre video passe Instagram, elle passera partout (TikTok, YouTube, etc.).</p>

            <div style="margin-top:12px">
                <div style="color:#E1306C;font-weight:600;font-size:0.85rem;margin-bottom:8px">
                    5 couches de detection Instagram :
                </div>
                <div class="step">
                    1. <span class="highlight">Perceptual Hashing (pHash)</span> — Compare une empreinte visuelle de chaque frame.
                    Le <span style="color:#FF6482">noise</span> et le <span style="color:#FFD60A">zoom</span> cassent ce hash.<br>
                    2. <span class="highlight">Content Matching (Deep Learning)</span> — Reseau de neurones qui reconnait le contenu
                    meme modifie. Le <span style="color:#FF453A">miroir</span> et le <span style="color:#30D158">crop</span> le perturbent.<br>
                    3. <span class="highlight">Audio Fingerprinting</span> — Empreinte audio unique.
                    Le <span style="color:#5E5CE6">pitch shift</span> et le changement de <span style="color:#64D2FF">vitesse</span> la modifient.<br>
                    4. <span class="highlight">Watermark Detection</span> — Detecte les watermarks TikTok/autres.
                    Le crop et le re-encoding les suppriment.<br>
                    5. <span class="highlight">Metadata Analysis</span> — Compare les metadonnees EXIF/MP4.
                    La <span style="color:#BF5AF2">randomisation meta</span> les remplace.
                </div>
            </div>

            <div style="margin-top:12px;padding:10px;background:#0A2F1C;border:1px solid #30D158;
                        border-radius:8px;color:#30D158;font-size:0.78rem">
                ✅ Le badge <b>"Safe Instagram"</b> (vert, ≥60%) signifie que votre video a suffisamment
                de modifications pour passer la detection d'Instagram — et donc de toutes les plateformes.
            </div>
            <div style="margin-top:6px;padding:10px;background:#2C2C2E;border:1px solid #3A3A3C;
                        border-radius:8px;color:#FF9F0A;font-size:0.78rem">
                ⚠️ Le badge <b>"Safe TikTok"</b> (orange, 30-59%) passe TikTok mais risque la detection
                sur Instagram Reels. Activez plus de modifications si vous ciblez Instagram.
            </div>
        </div>""", unsafe_allow_html=True)

    # Config values
    output_dir = st.session_state.get('cfg_output', 'outputs')
    intensity = st.session_state.get('cfg_intensity', 'medium')
    enabled_mods = {k: st.session_state.get(f"mod_{k}", True)
                    for k in ["noise","zoom","gamma","hue","hflip","crop","speed","pitch","fps","meta"]}

    # ===== IMPORT URL =====
    with tab_url:
        st.markdown("### 🔗 Importer depuis une URL")
        url = st.text_input("Colle un lien TikTok, Instagram ou YouTube",
                            placeholder="https://www.tiktok.com/@user/video/...", key="url_input")

        if url:
            plat = detect_platform(url)
            labels = {"tiktok":("TikTok","plat-tiktok"), "instagram":("Instagram","plat-instagram"),
                      "youtube":("YouTube","plat-youtube"), "other":("Autre","plat-other")}
            lbl, cls = labels.get(plat, ("Autre","plat-other"))
            st.markdown(f'<span class="plat {cls}">{lbl} detecte</span>', unsafe_allow_html=True)

        col_l, col_r = st.columns([1, 3])

        with col_l:
            if url and st.button("📥 Telecharger", type="primary", key="url_dl", use_container_width=True):
                with st.spinner("Telechargement + scraping stats..."):
                    path, err = download_from_url(url)
                    if err:
                        st.error(f"Erreur: {err}")
                    else:
                        st.session_state['url_video'] = path
                        # Scrape engagement stats
                        stats, stats_err = scrape_engagement_stats(url)
                        if stats:
                            st.session_state['url_engagement'] = stats
                            st.session_state['url_virality'] = calculate_virality_score(stats)
                        for k in ['url_analyses','url_folder']:
                            st.session_state.pop(k, None)
                        st.rerun()

            if 'url_video' in st.session_state and os.path.exists(st.session_state['url_video']):
                vp = st.session_state['url_video']
                st.markdown('<div class="compact-video">', unsafe_allow_html=True)
                st.video(vp)
                st.markdown('</div>', unsafe_allow_html=True)

                # Afficher le score de viralite engagement
                if 'url_virality' in st.session_state:
                    st.markdown(render_virality(st.session_state['url_virality']), unsafe_allow_html=True)

                nv = st.slider("Variations", 1, 15, 5, key="url_vars")
                if st.button("Generer les variations", type="primary", key="url_gen", use_container_width=True):
                    prog = st.progress(0); stat = st.empty()
                    try:
                        analyses, folder = run_generation(vp, nv, output_dir, intensity, enabled_mods, prog, stat)
                        st.session_state['url_analyses'] = analyses
                        st.session_state['url_folder'] = folder
                        stat.empty(); prog.empty()
                        st.success(f"✅ {len(analyses)} variations generees")
                    except Exception as e:
                        st.error(f"Erreur: {e}")

        with col_r:
            if 'url_analyses' in st.session_state:
                render_results(
                    st.session_state['url_analyses'],
                    st.session_state.get('url_folder',''),
                    "url",
                    virality=st.session_state.get('url_virality'),
                    captions_overlay=None,
                    original_texts=None,
                    descriptions=None
                )
            else:
                st.markdown("""<div style="background:#1C1C1E;border:1px solid #2C2C2E;border-radius:12px;
                    padding:32px;text-align:center;color:#48484A;margin-top:20px">
                    <div style="font-size:2.5rem;margin-bottom:10px">🔗</div>
                    <div style="font-size:1rem">Colle une URL pour commencer</div>
                    <div style="font-size:.75rem;margin-top:6px;color:#3A3A3C">TikTok · Instagram Reels · YouTube Shorts</div>
                </div>""", unsafe_allow_html=True)

    # ===== SINGLE =====
    with tab_single:
        col_l, col_r = st.columns([1, 3])

        with col_l:
            uploaded = st.file_uploader("📹 Video source", type=['mp4','mov','avi'], key="single_file")

            if uploaded:
                if 'single_temp' not in st.session_state:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    tmp.write(uploaded.read()); tmp.close()
                    st.session_state['single_temp'] = tmp.name
                    uploaded.seek(0)

                st.markdown('<div class="compact-video">', unsafe_allow_html=True)
                st.video(uploaded)
                st.markdown('</div>', unsafe_allow_html=True)

                nv = st.slider("Variations", 1, 15, 5, key="single_vars")
                if st.button("Generer les variations", type="primary", key="single_gen", use_container_width=True):
                    tp = st.session_state.get('single_temp')
                    if not tp or not os.path.exists(tp):
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                        tmp.write(uploaded.read()); tmp.close()
                        tp = tmp.name

                    prog = st.progress(0); stat = st.empty()
                    try:
                        analyses, folder = run_generation(tp, nv, output_dir, intensity, enabled_mods, prog, stat)
                        st.session_state['single_analyses'] = analyses
                        st.session_state['single_folder'] = folder
                        # OCR captions + descriptions
                        captions_overlay, original_texts = generate_captions_from_ocr(tp)
                        st.session_state['single_captions_overlay'] = captions_overlay
                        st.session_state['single_original_texts'] = original_texts
                        st.session_state['single_descriptions'] = generate_descriptions()
                        stat.empty(); prog.empty()
                        st.success(f"✅ {len(analyses)} variations generees")
                    except Exception as e:
                        st.error(f"Erreur: {e}")
            else:
                for k in ['single_temp']:
                    if k in st.session_state:
                        try: os.unlink(st.session_state[k])
                        except Exception: pass
                        del st.session_state[k]

        with col_r:
            if 'single_analyses' in st.session_state:
                render_results(
                    st.session_state['single_analyses'],
                    st.session_state.get('single_folder',''),
                    "single",
                    virality=None,
                    captions_overlay=st.session_state.get('single_captions_overlay'),
                    original_texts=st.session_state.get('single_original_texts'),
                    descriptions=st.session_state.get('single_descriptions')
                )

    # ===== BULK =====
    with tab_bulk:
        col_l, col_r = st.columns([1, 3])

        with col_l:
            files = st.file_uploader("📹 Plusieurs videos", type=['mp4','mov','avi'],
                                     accept_multiple_files=True, key="bulk_files")
            if files:
                if len(files) > 10:
                    st.warning("⚠️ Max 10 videos.")
                    files = files[:10]
                st.success(f"{len(files)} videos selectionnees")
                for f in files[:3]: st.caption(f"📹 {f.name}")
                if len(files) > 3: st.caption(f"... +{len(files)-3} autres")

                vpv = st.slider("Var / video", 1, 10, 3, key="bulk_vars")
                st.info(f"**{len(files) * vpv} videos** au total")

                if st.button("Lancer", type="primary", key="bulk_gen", use_container_width=True):
                    bf = get_dated_folder_name() + " BULK"
                    bp = os.path.join(output_dir, bf)
                    os.makedirs(bp, exist_ok=True)
                    prog = st.progress(0); stat = st.empty()
                    all_res = []
                    try:
                        from uniquifier import uniquify_video_ffmpeg
                        for vi, uf in enumerate(files):
                            vname = Path(uf.name).stem
                            stat.text(f"⏳ [{vi+1}/{len(files)}] {vname}")
                            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                            tmp.write(uf.read()); tmp.close()

                            vfolder = os.path.join(bp, vname)
                            os.makedirs(vfolder, exist_ok=True)
                            vr = {'name': vname, 'variations': [], 'success_count': 0}

                            for j in range(vpv):
                                op = os.path.join(vfolder, f"V{j+1:02d}.mp4")
                                r = uniquify_video_ffmpeg(tmp.name, op, intensity, enabled_mods)
                                if r["success"]:
                                    mods = r.get("modifications",{})
                                    a = estimate_uniqueness(mods)
                                    vr['variations'].append({
                                        'name': f"V{j+1:02d}", 'output_path': op,
                                        'uniqueness': a['uniqueness'], 'modifications': mods,
                                        'thumbnail': extract_thumbnail(op)
                                    })
                                    vr['success_count'] += 1

                            # OCR captions for this video
                            caps, orig = generate_captions_from_ocr(tmp.name)
                            vr['captions_overlay'] = caps
                            vr['original_texts'] = orig
                            vr['descriptions'] = generate_descriptions()

                            all_res.append(vr)
                            os.unlink(tmp.name)
                            prog.progress((vi+1)/len(files))

                        st.session_state['bulk_results'] = all_res
                        st.session_state['bulk_folder'] = bf
                        stat.empty()
                        st.success(f"✅ {sum(r['success_count'] for r in all_res)} videos")
                    except Exception as e:
                        st.error(f"Erreur: {e}")

        with col_r:
            if 'bulk_results' in st.session_state:
                results = st.session_state['bulk_results']
                bf = st.session_state.get('bulk_folder','')

                total = sum(r['success_count'] for r in results)
                allv = [v for r in results for v in r['variations']]
                avg = sum(v['uniqueness'] for v in allv)/len(allv) if allv else 0
                safe = sum(1 for v in allv if v['uniqueness'] >= 60)

                m1,m2,m3 = st.columns(3)
                m1.metric("📹 Total", total)
                m2.metric("📊 Moy.", f"{avg:.0f}%")
                m3.metric("✅ Safe Instagram", f"{safe}/{len(allv)}")

                # ZIP all
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for r in results:
                        for v in r['variations']:
                            p = v.get('output_path','')
                            if p and os.path.exists(p):
                                zf.write(p, f"{r['name']}/{v['name']}.mp4")
                buf.seek(0)
                st.download_button("📦 Tout telecharger (ZIP)", buf.getvalue(),
                                   file_name=f"{bf}.zip", mime="application/zip",
                                   key="zip_bulk", use_container_width=True)

                st.markdown("""<div class="legend">🟢 ≥60% = Safe Instagram &nbsp;|&nbsp; 🟠 30-59% = Safe TikTok seulement &nbsp;|&nbsp; 🔴 <30% = Risque</div>""", unsafe_allow_html=True)

                for r in results:
                    with st.expander(f"📹 {r['name']} — {r['success_count']} variations", expanded=True):
                        # HTML table grid
                        st.markdown(build_grid_html(r['variations']), unsafe_allow_html=True)

                        # Download buttons
                        dl_cols = st.columns(min(5, max(1, len(r['variations']))))
                        for i, v in enumerate(r['variations']):
                            p = v.get('output_path','')
                            if p and os.path.exists(p):
                                with dl_cols[i % 5]:
                                    with open(p, 'rb') as f:
                                        st.download_button(f"⬇ {v['name']}", f.read(),
                                            file_name=f"{r['name']}_{v['name']}.mp4",
                                            mime="video/mp4", key=f"dlb_{r['name']}_{v['name']}",
                                            use_container_width=True)

                        # Video previews
                        pcols = st.columns(min(3, max(1, len(r['variations']))))
                        for i, v in enumerate(r['variations']):
                            p = v.get('output_path','')
                            if p and os.path.exists(p):
                                with pcols[i % 3]:
                                    st.video(p)
                                    u = v['uniqueness']
                                    bc, _ = get_badge(u)
                                    st.markdown(f'<div style="text-align:center;margin-top:-6px;font-size:.75rem;color:#86868B">{v["name"]} <span class="{bc}" style="font-size:.68rem;padding:1px 6px">{u:.0f}%</span></div>', unsafe_allow_html=True)

                        # Captions + Descriptions per video
                        if r.get('captions_overlay'):
                            with st.expander("🎬 Captions (texte sur la video)", expanded=False):
                                if r.get('original_texts'):
                                    combined = " | ".join(r['original_texts'][:3])
                                    st.markdown(f'<div style="background:#2C2C2E;border-radius:8px;padding:8px;margin-bottom:8px;font-size:0.78rem;color:#86868B"><b style="color:#F5F5F7">Texte detecte :</b> {combined}</div>', unsafe_allow_html=True)
                                cc = st.columns(2)
                                for ci, cap in enumerate(r['captions_overlay']):
                                    with cc[ci % 2]:
                                        st.code(cap, language=None)

                        if r.get('descriptions'):
                            with st.expander("📝 Descriptions (texte sous la video)", expanded=False):
                                dc = st.columns(2)
                                for di, desc in enumerate(r['descriptions']):
                                    with dc[di % 2]:
                                        st.code(desc, language=None)
            else:
                st.info("👈 Upload plusieurs videos et lance le traitement")

    # ===== FERME (Farm Mode) =====
    with tab_farm:
        st.markdown("### 🏭 Mode Ferme — Traitement en masse")
        st.markdown('<div style="color:#86868B;font-size:0.82rem;margin-bottom:12px">Upload 50+ videos sources, lance le traitement, reviens le matin. Tout sera pret avec les scores.</div>', unsafe_allow_html=True)

        if not st.session_state.get('farm_running') and not st.session_state.get('farm_done'):
            # === UPLOAD + CONFIG ===
            farm_files = st.file_uploader(
                "📹 Videos sources (50+ supportees)",
                type=['mp4', 'mov', 'avi'],
                accept_multiple_files=True,
                key="farm_files"
            )

            if farm_files:
                st.success(f"📹 {len(farm_files)} videos selectionnees")
                for f in farm_files[:5]:
                    st.caption(f"  📹 {f.name}")
                if len(farm_files) > 5:
                    st.caption(f"  ... +{len(farm_files)-5} autres")

                fc1, fc2 = st.columns(2)
                with fc1:
                    farm_vpv = st.slider("Variations par video", 1, 20, 5, key="farm_vpv")
                with fc2:
                    farm_intensity = st.select_slider(
                        "Intensite Ferme", options=["low","medium","high"],
                        value="medium", key="farm_intensity"
                    )

                total_gen = len(farm_files) * farm_vpv
                est_seconds = total_gen * 8
                est_min = est_seconds // 60
                est_sec = est_seconds % 60

                st.markdown(f"""<div style="background:#1C1C1E;border:1px solid #2C2C2E;border-radius:12px;padding:14px;margin:10px 0">
                    <div style="display:flex;gap:20px;flex-wrap:wrap">
                        <div><span style="color:#86868B;font-size:0.75rem">Videos sources</span><br>
                             <span style="color:#F5F5F7;font-size:1.2rem;font-weight:700">{len(farm_files)}</span></div>
                        <div><span style="color:#86868B;font-size:0.75rem">Variations/video</span><br>
                             <span style="color:#F5F5F7;font-size:1.2rem;font-weight:700">{farm_vpv}</span></div>
                        <div><span style="color:#86868B;font-size:0.75rem">Total a generer</span><br>
                             <span style="color:#007AFF;font-size:1.2rem;font-weight:700">{total_gen}</span></div>
                        <div><span style="color:#86868B;font-size:0.75rem">Temps estime</span><br>
                             <span style="color:#FF9F0A;font-size:1.2rem;font-weight:700">~{est_min}m{est_sec:02d}s</span></div>
                    </div>
                </div>""", unsafe_allow_html=True)

                if st.button("🚀 Lancer la Ferme", type="primary", use_container_width=True, key="farm_start"):
                    # Save files to temp
                    temp_paths = []
                    for uf in farm_files:
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                        tmp.write(uf.read()); tmp.close()
                        temp_paths.append((uf.name, tmp.name))

                    st.session_state['farm_running'] = True
                    st.session_state['farm_results'] = []

                    # Processing loop
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    metrics_container = st.empty()

                    total_videos = len(temp_paths)
                    total_variations = total_videos * farm_vpv
                    completed = 0
                    all_scores = []
                    start_time = datetime.now()

                    from uniquifier import uniquify_video_ffmpeg

                    farm_folder = get_dated_folder_name() + " FERME"
                    farm_path = os.path.join(output_dir, farm_folder)
                    os.makedirs(farm_path, exist_ok=True)

                    farm_results = []

                    for vi, (vname_full, vpath) in enumerate(temp_paths):
                        video_name = Path(vname_full).stem
                        video_folder = os.path.join(farm_path, video_name)
                        os.makedirs(video_folder, exist_ok=True)

                        video_result = {
                            'name': video_name,
                            'variations': [],
                            'success_count': 0
                        }

                        fi = st.session_state.get('farm_intensity', 'medium')

                        for j in range(farm_vpv):
                            status_text.markdown(f"""<div style="background:#1C1C1E;border:1px solid #2C2C2E;
                                border-radius:8px;padding:8px 12px;font-size:0.85rem;color:#F5F5F7">
                                ⏳ <b>[{vi+1}/{total_videos}]</b> {video_name} — V{j+1:02d}/{farm_vpv}
                            </div>""", unsafe_allow_html=True)

                            out = os.path.join(video_folder, f"V{j+1:02d}.mp4")
                            r = uniquify_video_ffmpeg(vpath, out, fi, enabled_mods)

                            if r["success"]:
                                mods = r.get("modifications", {})
                                a = estimate_uniqueness(mods)
                                video_result['variations'].append({
                                    'name': f"V{j+1:02d}",
                                    'output_path': out,
                                    'uniqueness': a['uniqueness'],
                                    'modifications': mods,
                                    'thumbnail': extract_thumbnail(out)
                                })
                                video_result['success_count'] += 1
                                all_scores.append(a['uniqueness'])

                            completed += 1
                            progress_bar.progress(completed / total_variations)

                            # Update metrics
                            elapsed = (datetime.now() - start_time).total_seconds()
                            rate = completed / max(elapsed, 1)
                            remaining = (total_variations - completed) / max(rate, 0.01)
                            avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
                            safe_count = sum(1 for s in all_scores if s >= 60)

                            with metrics_container.container():
                                mc1, mc2, mc3, mc4 = st.columns(4)
                                mc1.metric("✅ Termine", f"{completed}/{total_variations}")
                                mc2.metric("📊 Score moyen", f"{avg_score:.0f}%")
                                mc3.metric("⏱️ Restant", f"~{int(remaining//60)}m{int(remaining%60):02d}s")
                                mc4.metric("🟢 Safe Instagram", f"{safe_count}/{len(all_scores)}")

                        farm_results.append(video_result)

                        # Cleanup temp
                        try: os.unlink(vpath)
                        except Exception: pass

                    st.session_state['farm_results'] = farm_results
                    st.session_state['farm_folder'] = farm_folder
                    st.session_state['farm_running'] = False
                    st.session_state['farm_done'] = True
                    st.rerun()

        elif st.session_state.get('farm_done'):
            # === RESULTS ===
            results = st.session_state.get('farm_results', [])
            farm_folder = st.session_state.get('farm_folder', '')

            if results:
                allv = [v for r in results for v in r['variations']]
                total = len(allv)
                avg = sum(v['uniqueness'] for v in allv) / len(allv) if allv else 0
                safe = sum(1 for v in allv if v['uniqueness'] >= 60)

                st.markdown(f"""<div style="background:#0A2F1C;border:1px solid #30D158;border-radius:12px;
                    padding:14px;margin-bottom:12px;text-align:center">
                    <span style="font-size:1.2rem;font-weight:700;color:#30D158">
                        ✅ Ferme terminee — {total} videos generees
                    </span>
                </div>""", unsafe_allow_html=True)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("📹 Videos sources", len(results))
                m2.metric("🎬 Total genere", total)
                m3.metric("📊 Score moyen", f"{avg:.0f}%")
                m4.metric("🟢 Safe Instagram", f"{safe}/{total}")

                # Global ZIP
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for r in results:
                        for v in r['variations']:
                            p = v.get('output_path', '')
                            if p and os.path.exists(p):
                                zf.write(p, f"{r['name']}/{v['name']}.mp4")
                buf.seek(0)
                st.download_button("📦 Tout telecharger (ZIP)", buf.getvalue(),
                                   file_name=f"{farm_folder}.zip", mime="application/zip",
                                   key="zip_farm", use_container_width=True)

                st.markdown("""<div class="legend">🟢 ≥60% = Safe Instagram &nbsp;|&nbsp; 🟠 30-59% = Safe TikTok seulement &nbsp;|&nbsp; 🔴 <30% = Risque</div>""", unsafe_allow_html=True)

                # Per-video expandable sections
                for r in results:
                    with st.expander(f"📹 {r['name']} — {r['success_count']} variations", expanded=False):
                        st.markdown(build_grid_html(r['variations']), unsafe_allow_html=True)

                        # Download buttons
                        if r['variations']:
                            dl_cols = st.columns(min(5, len(r['variations'])))
                            for i, v in enumerate(r['variations']):
                                p = v.get('output_path','')
                                if p and os.path.exists(p):
                                    with dl_cols[i % 5]:
                                        with open(p, 'rb') as f:
                                            st.download_button(f"⬇ {v['name']}", f.read(),
                                                file_name=f"{r['name']}_{v['name']}.mp4",
                                                mime="video/mp4", key=f"dlf_{r['name']}_{v['name']}",
                                                use_container_width=True)

                        # Video previews
                        if r['variations']:
                            pcols = st.columns(min(3, len(r['variations'])))
                            for i, v in enumerate(r['variations']):
                                p = v.get('output_path','')
                                if p and os.path.exists(p):
                                    with pcols[i % 3]:
                                        st.video(p)
                                        u = v['uniqueness']
                                        bc, _ = get_badge(u)
                                        st.markdown(f'<div style="text-align:center;margin-top:-6px;font-size:.75rem;color:#86868B">{v["name"]} <span class="{bc}" style="font-size:.68rem;padding:1px 6px">{u:.0f}%</span></div>', unsafe_allow_html=True)

                # Reset button
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                if st.button("🔄 Nouvelle session Ferme", key="farm_reset", use_container_width=True):
                    for k in ['farm_results', 'farm_done', 'farm_folder', 'farm_running']:
                        st.session_state.pop(k, None)
                    st.rerun()

    # ===== STATISTIQUES =====
    with tab_stats:
        st.markdown("### 📊 Statistiques")
        if os.path.exists(output_dir):
            vids = list(Path(output_dir).rglob("*.mp4"))
            folders = [f for f in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, f))]
            sz = sum(f.stat().st_size for f in vids) / (1024*1024)
            c1,c2,c3 = st.columns(3)
            c1.metric("📁 Sessions", len(folders))
            c2.metric("📹 Videos", len(vids))
            c3.metric("💾 Espace", f"{sz:.1f} MB")
            st.markdown("---")

            # Categorize folders
            farm_folders = [f for f in sorted(folders, reverse=True) if "FERME" in f]
            bulk_folders = [f for f in sorted(folders, reverse=True) if "BULK" in f]
            other_folders = [f for f in sorted(folders, reverse=True) if "FERME" not in f and "BULK" not in f]

            if farm_folders:
                st.markdown("#### 🏭 Sessions Ferme")
                for f in farm_folders:
                    n = len(list(Path(os.path.join(output_dir,f)).rglob("*.mp4")))
                    st.text(f"  📁 {f} — {n} videos")

            if bulk_folders:
                st.markdown("#### 📦 Sessions Bulk")
                for f in bulk_folders:
                    n = len(list(Path(os.path.join(output_dir,f)).rglob("*.mp4")))
                    st.text(f"  📁 {f} — {n} videos")

            if other_folders:
                st.markdown("#### 📤 Sessions Single / Import")
                for f in other_folders:
                    n = len(list(Path(os.path.join(output_dir,f)).rglob("*.mp4")))
                    st.text(f"  📁 {f} — {n} videos")
        else:
            st.info("Aucune donnee — lance une generation pour voir les stats")


if __name__ == "__main__":
    main()
