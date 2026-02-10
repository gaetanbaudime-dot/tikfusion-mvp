"""
TikFusion v3 — Professional video uniquifier
Import URL | Score de Viralité | Analyse Captions
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

    /* Result grid */
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
    .rg-tags { line-height: 1.6; }
    .rg-score { text-align: center; white-space: nowrap; }
    .rg-thumb { height: 80px; border-radius: 6px; object-fit: cover; }

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
    if score >= 60: return 'badge-safe'
    if score >= 30: return 'badge-warning'
    return 'badge-danger'


def extract_thumbnail(video_path):
    thumb = video_path + ".thumb.jpg"
    if os.path.exists(thumb): return thumb
    try:
        subprocess.run(["ffmpeg","-y","-i",video_path,"-vf","thumbnail,scale=120:-1",
                        "-frames:v","1","-q:v","5",thumb], capture_output=True, timeout=10)
        return thumb if os.path.exists(thumb) else None
    except: return None


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
            return None, "Aucun fichier téléchargé"

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
                return None, "Conversion MP4 échouée"

        shutil.rmtree(tmpdir, ignore_errors=True)
        if os.path.exists(final.name) and os.path.getsize(final.name) > 0:
            return final.name, None
        return None, "Fichier vide"
    except subprocess.TimeoutExpired:
        return None, "Timeout — vidéo trop longue"
    except Exception as e:
        return None, str(e)


# ============ VIRALITY ANALYSIS ============

def analyze_virality(video_path):
    info = {}
    try:
        r = subprocess.run(["ffprobe","-v","quiet","-print_format","json",
                            "-show_format","-show_streams",video_path],
                           capture_output=True, text=True, timeout=30)
        info = json.loads(r.stdout) if r.returncode == 0 else {}
    except: pass

    score = 0
    breakdown = []
    tips = []
    why = []

    # Duration (25 pts)
    try: duration = float(info.get('format',{}).get('duration',0))
    except: duration = 0

    if 7 <= duration <= 15:
        pts = 25; breakdown.append(("⏱️ Durée", f"{duration:.0f}s — hook court", pts, 25))
        why.append("Durée idéale pour un hook viral (7-15s = rétention max)")
    elif 15 < duration <= 30:
        pts = 22; breakdown.append(("⏱️ Durée", f"{duration:.0f}s — optimal", pts, 25))
        why.append("Durée optimale TikTok — assez court pour garder l'attention")
    elif 30 < duration <= 60:
        pts = 18; breakdown.append(("⏱️ Durée", f"{duration:.0f}s — Reels", pts, 25))
    elif duration > 60:
        pts = 8; breakdown.append(("⏱️ Durée", f"{duration:.0f}s — long", pts, 25))
        tips.append("Couper à <30s pour maximiser la rétention")
    else:
        pts = 5; breakdown.append(("⏱️ Durée", "Inconnue", pts, 25))
    score += pts

    # Format (20 pts)
    vs = None; aus = None
    for s in info.get('streams', []):
        if s.get('codec_type') == 'video' and not vs: vs = s
        if s.get('codec_type') == 'audio' and not aus: aus = s

    if vs:
        w, h = int(vs.get('width',0)), int(vs.get('height',0))
        if h > w and h >= 1920:
            pts = 20; breakdown.append(("📐 Format", f"{w}x{h} — vertical HD", pts, 20))
            why.append("Format 9:16 vertical HD — plein écran sur mobile")
        elif h > w:
            pts = 15; breakdown.append(("📐 Format", f"{w}x{h} — vertical", pts, 20))
            tips.append("Passer en 1080x1920 pour qualité max")
        elif w == h:
            pts = 10; breakdown.append(("📐 Format", f"{w}x{h} — carré", pts, 20))
            tips.append("Format vertical (9:16) recommandé")
        else:
            pts = 5; breakdown.append(("📐 Format", f"{w}x{h} — horizontal", pts, 20))
            tips.append("Recadrer en vertical pour Reels/TikTok")
        score += pts
    else:
        score += 5; breakdown.append(("📐 Format", "Non détecté", 5, 20))

    # Audio (20 pts)
    if aus:
        pts = 20; breakdown.append(("🔊 Audio", "Présent", pts, 20))
        why.append("Audio présent — essentiel pour l'engagement (+70% de rétention)")
    else:
        pts = 2; breakdown.append(("🔊 Audio", "Absent", pts, 20))
        tips.append("Ajouter audio (musique trending ou voiceover)")
    score += pts

    # Bitrate (15 pts)
    try:
        br = int(info.get('format',{}).get('bit_rate',0)) / 1000
        if br >= 5000: pts = 15; breakdown.append(("🎬 Qualité", f"{br:.0f}kbps", pts, 15))
        elif br >= 2000: pts = 12; breakdown.append(("🎬 Qualité", f"{br:.0f}kbps", pts, 15))
        elif br >= 1000: pts = 8; breakdown.append(("🎬 Qualité", f"{br:.0f}kbps", pts, 15))
        else: pts = 4; breakdown.append(("🎬 Qualité", f"{br:.0f}kbps", pts, 15)); tips.append("Augmenter le bitrate")
        score += pts
    except: score += 5; breakdown.append(("🎬 Qualité", "?", 5, 15))

    # FPS (10 pts)
    if vs:
        try:
            n, d = vs.get('r_frame_rate','30/1').split('/')
            fps = int(n) / max(int(d), 1)
            if fps >= 30: pts = 10; breakdown.append(("🎞️ FPS", f"{fps:.0f}", pts, 10))
            elif fps >= 24: pts = 7; breakdown.append(("🎞️ FPS", f"{fps:.0f}", pts, 10))
            else: pts = 3; breakdown.append(("🎞️ FPS", f"{fps:.0f}", pts, 10)); tips.append("Filmer en 30fps+")
            score += pts
        except: score += 5; breakdown.append(("🎞️ FPS", "?", 5, 10))

    # Size (10 pts)
    try:
        sz = os.path.getsize(video_path) / (1024*1024)
        if sz <= 10: pts = 10; breakdown.append(("📦 Taille", f"{sz:.1f}MB", pts, 10))
        elif sz <= 50: pts = 7; breakdown.append(("📦 Taille", f"{sz:.1f}MB", pts, 10))
        else: pts = 3; breakdown.append(("📦 Taille", f"{sz:.1f}MB", pts, 10)); tips.append("Compresser la vidéo")
        score += pts
    except: score += 5; breakdown.append(("📦 Taille", "?", 5, 10))

    return {'score': min(score, 100), 'breakdown': breakdown, 'tips': tips, 'why': why,
            'duration': duration, 'has_audio': aus is not None,
            'resolution': f"{vs.get('width','?')}x{vs.get('height','?')}" if vs else "?"}


def render_virality(analysis):
    s = analysis['score']
    b = get_badge(s)
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
        why = f'<div class="vir-why"><div style="font-weight:600;margin-bottom:4px">Pourquoi ça marche :</div>{items}</div>'

    return f"""<div class="vir-card"><div class="vir-head">
        <span class="vir-title">🔥 Score de Viralité</span>
        <span class="{b}" style="font-size:1rem;padding:5px 14px">{s}/100</span>
    </div>{rows}{why}{tips}</div>"""


# ============ CAPTION GENERATION ============

def generate_captions(duration=0):
    hooks_curiosite = [
        "Personne ne parle de ça mais...",
        "Ce que personne ne te dit sur...",
        "La vérité que tout le monde ignore",
        "Tu ne devineras jamais ce qui se passe",
        "Le secret que les pros cachent",
    ]
    hooks_valeur = [
        "3 astuces que j'utilise tous les jours",
        "Fais ça et remercie-moi plus tard",
        "La méthode qui a tout changé pour moi",
        "L'astuce que j'aurais aimé connaître avant",
        "Voici comment faire en 30 secondes",
    ]
    hooks_emotion = [
        "Ça m'a laissé sans voix...",
        "Quand tu réalises que...",
        "POV: tu découvres ça pour la première fois",
        "Avant vs Après — la différence est folle",
        "Le moment où tout a basculé",
    ]
    hooks_urgence = [
        "Sauvegarde avant que ça disparaisse",
        "Stop le scroll — regarde ça",
        "Si tu vois cette vidéo c'est un signe",
        "Ne rate pas la fin surtout",
        "Tu passes à côté si tu scrolles",
    ]
    ctas = [
        "Follow pour plus 🔥",
        "Like si tu veux la partie 2",
        "Commente 🔥 si ça t'a aidé",
        "Enregistre pour plus tard 📌",
        "Partage à quelqu'un qui en a besoin",
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

    # Take 2-3 from each category for variety
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
            v = f"{hook}\n\n💡 Regarde jusqu'à la fin\n\n{cta}\n\n{tag}"
        else:
            v = f"{hook}\n\n⬇️ Tout est dans la vidéo\n\n{cta}\n\n{tag}"
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

def render_results(analyses, folder, prefix, virality=None, captions=None):
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

    st.markdown("""<div class="legend">🟢 ≥60% = Safe TikTok+Instagram &nbsp;|&nbsp; 🟠 30-59% = Safe TikTok &nbsp;|&nbsp; 🔴 <30% = Risque</div>""", unsafe_allow_html=True)

    # Build HTML table grid (name + tags + score + thumbnail) — all in ONE block
    grid_html = '<table class="rg-table"><tr class="rg-head"><td style="width:36px">#</td><td>Modifications</td><td style="width:56px">Score</td><td style="width:90px">Aperçu</td></tr>'

    for a in analyses:
        u = a['uniqueness']
        badge = get_badge(u)
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

        grid_html += f"""<tr class="rg-row">
            <td><span class="rg-name">{a['name']}</span></td>
            <td><span class="rg-tags">{tags_html}</span></td>
            <td class="rg-score"><span class="{badge}">{u:.0f}%</span></td>
            <td style="text-align:center">{thumb_img}</td>
        </tr>\n"""

    grid_html += '</table>'
    st.markdown(grid_html, unsafe_allow_html=True)

    # Download buttons strip (5 per line, tight)
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
    st.markdown("##### 🎬 Aperçus — vérifier les modifications")
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
                    badge = get_badge(u)
                    st.markdown(f'<div style="text-align:center;margin-top:-6px"><span class="rg-name">{a["name"]}</span> &nbsp; <span class="{badge}" style="font-size:.72rem;padding:2px 8px">{u:.0f}%</span></div>', unsafe_allow_html=True)

    # Virality
    if virality:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        with st.expander("🔥 Analyse de Viralité — Pourquoi ça marche", expanded=False):
            st.markdown(render_virality(virality), unsafe_allow_html=True)

    # Captions
    if captions:
        with st.expander("📝 10 Variantes de Captions virales", expanded=False):
            cap_cols = st.columns(2)
            for i, cap in enumerate(captions):
                with cap_cols[i % 2]:
                    st.code(cap, language=None)


# ============ MAIN ============

def main():
    st.markdown("""<div class="header-bar">
        <span class="header-logo">LTP</span>
        <span class="header-title">TikFusion</span>
    </div>""", unsafe_allow_html=True)

    tab_url, tab_single, tab_bulk, tab_stats, tab_config = st.tabs([
        "🔗 Import", "📤 Single", "📦 Bulk", "📊 Stats", "⚙️ Config"
    ])

    # ===== CONFIG (first for variables) =====
    with tab_config:
        st.markdown("### ⚙️ Configuration")
        c1, c2 = st.columns(2)
        with c1: output_dir = st.text_input("📁 Dossier de sortie", value="outputs", key="cfg_output")
        with c2: intensity = st.select_slider("🎚️ Intensité", options=["low","medium","high"], value="medium", key="cfg_intensity")

        st.markdown("---")
        st.markdown("### 🎛️ Modifications anti-détection")

        st.markdown("#### 👁️ Anti Hash Visuel — *~30-35% de la détection*")
        v1,v2 = st.columns(2)
        with v1:
            mod_noise = st.toggle("📡 Pixel Noise", value=True, key="mod_noise", help="Bruit invisible. Le plus efficace contre pHash.")
            mod_zoom = st.toggle("🔍 Zoom", value=True, key="mod_zoom", help="Zoom léger. Repositionne les pixels.")
        with v2:
            mod_gamma = st.toggle("🌗 Gamma", value=True, key="mod_gamma", help="Modifie la luminosité globale.")
            mod_hue = st.toggle("🎨 Couleur", value=True, key="mod_hue", help="Décale la teinte.")

        st.markdown("#### 🧠 Anti Deep Learning — *~25-30%*")
        s1,s2 = st.columns(2)
        with s1:
            mod_hflip = st.toggle("🪞 Miroir", value=True, key="mod_hflip", help="Inverse horizontalement.")
            mod_crop = st.toggle("✂️ Crop", value=True, key="mod_crop", help="Coupe les bords.")
        with s2:
            mod_speed = st.toggle("🔄 Vitesse", value=True, key="mod_speed", help="Change la vitesse.")

        st.markdown("#### 🔊 Anti Fingerprint Audio — *~20-25%*")
        a1,a2 = st.columns(2)
        with a1: mod_pitch = st.toggle("🎵 Pitch", value=True, key="mod_pitch", help="Décale la fréquence audio.")
        with a2: mod_fps = st.toggle("🎞️ FPS", value=True, key="mod_fps", help="Change le framerate.")

        st.markdown("#### 🏷️ Metadata")
        mod_meta = st.toggle("🏷️ Metadata aléatoires", value=True, key="mod_meta", help="Randomise les métadonnées.")

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
        bc = get_badge(ps)
        st.markdown(f"""<div style="background:#1C1C1E;border:1px solid #2C2C2E;border-radius:12px;padding:14px;margin:8px 0">
            <div style="display:flex;align-items:center;justify-content:space-between">
                <span style="font-size:1rem;font-weight:600;color:#F5F5F7">📊 Score estimé moyen</span>
                <span class="{bc}" style="font-size:1.1rem;padding:5px 14px">{ps}%</span>
            </div>
            <div style="color:#86868B;font-size:.72rem;margin-top:6px">{" · ".join(d)}</div>
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
            st.markdown(f'<span class="plat {cls}">{lbl} détecté</span>', unsafe_allow_html=True)

        col_l, col_r = st.columns([1, 3])

        with col_l:
            if url and st.button("📥 Télécharger", type="primary", key="url_dl", use_container_width=True):
                with st.spinner("Téléchargement..."):
                    path, err = download_from_url(url)
                    if err:
                        st.error(f"Erreur: {err}")
                    else:
                        st.session_state['url_video'] = path
                        for k in ['url_analyses','url_virality','url_captions','url_folder']:
                            st.session_state.pop(k, None)
                        st.rerun()

            if 'url_video' in st.session_state and os.path.exists(st.session_state['url_video']):
                vp = st.session_state['url_video']
                st.markdown('<div class="compact-video">', unsafe_allow_html=True)
                st.video(vp)
                st.markdown('</div>', unsafe_allow_html=True)

                # Auto virality
                if 'url_virality' not in st.session_state:
                    st.session_state['url_virality'] = analyze_virality(vp)
                st.markdown(render_virality(st.session_state['url_virality']), unsafe_allow_html=True)

                nv = st.slider("Variations", 1, 15, 5, key="url_vars")
                if st.button("Générer les variations", type="primary", key="url_gen", use_container_width=True):
                    prog = st.progress(0); stat = st.empty()
                    try:
                        analyses, folder = run_generation(vp, nv, output_dir, intensity, enabled_mods, prog, stat)
                        st.session_state['url_analyses'] = analyses
                        st.session_state['url_folder'] = folder
                        vir = st.session_state.get('url_virality', {})
                        st.session_state['url_captions'] = generate_captions(vir.get('duration', 0))
                        stat.empty(); prog.empty()
                        st.success(f"✅ {len(analyses)} variations générées")
                    except Exception as e:
                        st.error(f"Erreur: {e}")

        with col_r:
            if 'url_analyses' in st.session_state:
                render_results(st.session_state['url_analyses'], st.session_state.get('url_folder',''),
                               "url", st.session_state.get('url_virality'), st.session_state.get('url_captions'))
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
            uploaded = st.file_uploader("📹 Vidéo source", type=['mp4','mov','avi'], key="single_file")

            if uploaded:
                if 'single_temp' not in st.session_state:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    tmp.write(uploaded.read()); tmp.close()
                    st.session_state['single_temp'] = tmp.name
                    uploaded.seek(0)

                st.markdown('<div class="compact-video">', unsafe_allow_html=True)
                st.video(uploaded)
                st.markdown('</div>', unsafe_allow_html=True)

                tp = st.session_state.get('single_temp')
                if tp and os.path.exists(tp):
                    if 'single_virality' not in st.session_state:
                        st.session_state['single_virality'] = analyze_virality(tp)
                    st.markdown(render_virality(st.session_state['single_virality']), unsafe_allow_html=True)

                nv = st.slider("Variations", 1, 15, 5, key="single_vars")
                if st.button("Générer les variations", type="primary", key="single_gen", use_container_width=True):
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
                        vir = st.session_state.get('single_virality', {})
                        st.session_state['single_captions'] = generate_captions(vir.get('duration', 0))
                        stat.empty(); prog.empty()
                        st.success(f"✅ {len(analyses)} variations générées")
                    except Exception as e:
                        st.error(f"Erreur: {e}")
            else:
                for k in ['single_temp','single_virality']:
                    if k in st.session_state:
                        if k == 'single_temp':
                            try: os.unlink(st.session_state[k])
                            except: pass
                        del st.session_state[k]

        with col_r:
            if 'single_analyses' in st.session_state:
                render_results(st.session_state['single_analyses'], st.session_state.get('single_folder',''),
                               "single", st.session_state.get('single_virality'), st.session_state.get('single_captions'))

    # ===== BULK =====
    with tab_bulk:
        col_l, col_r = st.columns([1, 3])

        with col_l:
            files = st.file_uploader("📹 Plusieurs vidéos", type=['mp4','mov','avi'],
                                     accept_multiple_files=True, key="bulk_files")
            if files:
                if len(files) > 10:
                    st.warning("⚠️ Max 10 vidéos.")
                    files = files[:10]
                st.success(f"{len(files)} vidéos sélectionnées")
                for f in files[:3]: st.caption(f"📹 {f.name}")
                if len(files) > 3: st.caption(f"... +{len(files)-3} autres")

                vpv = st.slider("Var / vidéo", 1, 10, 3, key="bulk_vars")
                st.info(f"**{len(files) * vpv} vidéos** au total")

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

                            all_res.append(vr)
                            os.unlink(tmp.name)
                            prog.progress((vi+1)/len(files))

                        st.session_state['bulk_results'] = all_res
                        st.session_state['bulk_folder'] = bf
                        stat.empty()
                        st.success(f"✅ {sum(r['success_count'] for r in all_res)} vidéos")
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
                m3.metric("✅ Safe", f"{safe}/{len(allv)}")

                # ZIP all
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for r in results:
                        for v in r['variations']:
                            p = v.get('output_path','')
                            if p and os.path.exists(p):
                                zf.write(p, f"{r['name']}/{v['name']}.mp4")
                buf.seek(0)
                st.download_button("📦 Tout télécharger (ZIP)", buf.getvalue(),
                                   file_name=f"{bf}.zip", mime="application/zip",
                                   key="zip_bulk", use_container_width=True)

                st.markdown("""<div class="legend">🟢 ≥60% = Safe &nbsp;|&nbsp; 🟠 30-59% = Attention &nbsp;|&nbsp; 🔴 <30% = Risque</div>""", unsafe_allow_html=True)

                for r in results:
                    with st.expander(f"📹 {r['name']} — {r['success_count']} variations", expanded=True):
                        # Build grid HTML table
                        grid_html = '<table class="rg-table"><tr class="rg-head"><td style="width:36px">#</td><td>Modifications</td><td style="width:56px">Score</td><td style="width:90px">Aperçu</td></tr>'
                        for v in r['variations']:
                            u = v['uniqueness']
                            badge = get_badge(u)
                            tags_html = format_tags(v.get('modifications',{}))
                            t_img = '<span style="color:#48484A;font-size:.7rem">—</span>'
                            t = v.get('thumbnail')
                            if t and os.path.exists(t):
                                b = thumb_b64(t)
                                if b: t_img = f'<img src="data:image/jpeg;base64,{b}" class="rg-thumb" />'
                            grid_html += f"""<tr class="rg-row">
                                <td><span class="rg-name">{v['name']}</span></td>
                                <td><span class="rg-tags">{tags_html}</span></td>
                                <td class="rg-score"><span class="{badge}">{u:.0f}%</span></td>
                                <td style="text-align:center">{t_img}</td>
                            </tr>\n"""
                        grid_html += '</table>'
                        st.markdown(grid_html, unsafe_allow_html=True)

                        # Download buttons
                        cols = st.columns(min(5, len(r['variations'])))
                        for i, v in enumerate(r['variations']):
                            p = v.get('output_path','')
                            if p and os.path.exists(p):
                                with cols[i % 5]:
                                    with open(p, 'rb') as f:
                                        st.download_button(f"⬇ {v['name']}", f.read(),
                                            file_name=f"{r['name']}_{v['name']}.mp4",
                                            mime="video/mp4", key=f"dlb_{r['name']}_{v['name']}",
                                            use_container_width=True)

                        # Video previews
                        pcols = st.columns(min(3, len(r['variations'])))
                        for i, v in enumerate(r['variations']):
                            p = v.get('output_path','')
                            if p and os.path.exists(p):
                                with pcols[i % 3]:
                                    st.video(p)
                                    st.markdown(f'<div style="text-align:center;margin-top:-6px;font-size:.75rem;color:#86868B">{v["name"]}</div>', unsafe_allow_html=True)
            else:
                st.info("👈 Upload plusieurs vidéos et lance le traitement")

    # ===== STATS =====
    with tab_stats:
        st.markdown("### 📊 Statistiques")
        if os.path.exists(output_dir):
            vids = list(Path(output_dir).rglob("*.mp4"))
            folders = [f for f in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, f))]
            sz = sum(f.stat().st_size for f in vids) / (1024*1024)
            c1,c2,c3 = st.columns(3)
            c1.metric("📁 Sessions", len(folders))
            c2.metric("📹 Vidéos", len(vids))
            c3.metric("💾 Espace", f"{sz:.1f} MB")
            st.markdown("---")
            for f in sorted(folders, reverse=True):
                n = len(list(Path(os.path.join(output_dir,f)).rglob("*.mp4")))
                st.text(f"  📁 {f} — {n} vidéos")


if __name__ == "__main__":
    main()
