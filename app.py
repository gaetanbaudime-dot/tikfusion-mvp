"""
TikFusion MVP — Video uniquifier for Instagram / TikTok / YouTube
Single | Bulk | Ferme | Stats | Config
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
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import (
    save_session, save_variation, get_analytics, init_db,
)

from uniqueness_checker import UniquenessChecker

init_db()
_uniqueness_checker = UniquenessChecker()

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
    .preview-grid video { border-radius: 10px; max-height: 320px; }
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


def _get_ffmpeg():
    """Get ffmpeg binary path (cached)"""
    if not hasattr(_get_ffmpeg, '_path'):
        try:
            from uniquifier import FFMPEG_BIN
            _get_ffmpeg._path = FFMPEG_BIN
        except Exception:
            _get_ffmpeg._path = shutil.which("ffmpeg") or "ffmpeg"
    return _get_ffmpeg._path


def _check_ffmpeg():
    """Check FFmpeg is available and return (ok, path, version_or_error)"""
    ffmpeg = _get_ffmpeg()
    try:
        r = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            version_line = r.stdout.split('\n')[0] if r.stdout else "OK"
            return True, ffmpeg, version_line
        return False, ffmpeg, r.stderr[:200] if r.stderr else "returncode != 0"
    except FileNotFoundError:
        return False, ffmpeg, f"Binaire introuvable: {ffmpeg}"
    except Exception as e:
        return False, ffmpeg, str(e)


def extract_thumbnail(video_path):
    thumb = video_path + ".thumb.jpg"
    if os.path.exists(thumb): return thumb
    try:
        subprocess.run([_get_ffmpeg(),"-y","-i",video_path,"-vf","thumbnail,scale=160:-1",
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


def build_zip_from_analyses(analyses):
    """ZIP en memoire a partir d'une liste d'analyses (Single/URL)"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for a in analyses:
            p = a.get('output_path', '')
            if p and os.path.exists(p):
                zf.write(p, f"{a['name']}.mp4")
    buf.seek(0)
    return buf.getvalue()


def build_zip_from_bulk_results(results, filter_safe=False):
    """ZIP en memoire a partir des resultats bulk/farm (video_name/V01.mp4)"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for r in results:
            for v in r['variations']:
                if filter_safe and v['uniqueness'] < 60:
                    continue
                p = v.get('output_path', '')
                if p and os.path.exists(p):
                    zf.write(p, f"{r['name']}/{v['name']}.mp4")
    buf.seek(0)
    return buf.getvalue()



# ============ GENERATION ENGINE (parallel + real scoring + SQLite) ============

def run_generation(input_path, num_vars, output_dir, intensity, enabled_mods, progress_bar, status_el,
                   session_mode="single", source_url=None, source_platform=None, virality_score=None):
    from uniquifier import uniquify_video_ffmpeg, FFMPEG_BIN

    # Check FFmpeg is available
    ok, ffpath, info = _check_ffmpeg()
    if not ok:
        st.error(f"FFmpeg non disponible ({ffpath}): {info}")
        st.info("Installe `imageio-ffmpeg` (pip) ou `ffmpeg` (systeme).")
        return [], "error"

    folder = get_dated_folder_name()
    out_dir = os.path.join(output_dir, folder)
    os.makedirs(out_dir, exist_ok=True)

    # Prepare all output paths
    tasks = []
    for i in range(num_vars):
        out = os.path.join(out_dir, f"V{i+1:02d}.mp4")
        tasks.append((i, input_path, out, intensity, enabled_mods))

    # Parallel generation (3 workers)
    raw_results = [None] * num_vars
    errors = []
    completed = 0

    def _worker(args):
        idx, inp, outp, intens, mods = args
        return idx, uniquify_video_ffmpeg(inp, outp, intens, mods)

    max_workers = min(3, num_vars)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_worker, t): t[0] for t in tasks}
        for future in as_completed(futures):
            idx, r = future.result()
            raw_results[idx] = r
            if not r.get("success"):
                errors.append(f"V{idx+1:02d}: {r.get('error', 'unknown')[:150]}")
            completed += 1
            progress_bar.progress(completed / num_vars)
            status_el.text(f"⏳ {completed}/{num_vars} genere(s)...")

    # Show errors if any
    if errors and not any(r and r.get("success") for r in raw_results):
        st.error("Toutes les variations ont echoue. Erreur FFmpeg:")
        st.code(errors[0], language="text")
        return [], "error"

    # Process results + real uniqueness check + SQLite persist
    session_id = save_session(
        mode=session_mode, source_url=source_url,
        source_platform=source_platform, virality_score=virality_score,
        folder_name=folder, num_variations=num_vars, intensity=intensity
    )

    results = []
    for i, r in enumerate(raw_results):
        if r and r["success"]:
            mods = r.get("modifications", {})
            out = r["output_path"]

            # Formula-based scoring (consistent across Single/Bulk/Farm)
            a = estimate_uniqueness(mods)

            a['name'] = Path(out).stem
            a['modifications'] = mods
            a['output_path'] = out
            a['thumbnail'] = extract_thumbnail(out)

            # Persist to SQLite
            save_variation(
                session_id=session_id, name=a['name'], output_path=out,
                uniqueness_score=a['uniqueness'],
                tiktok_score=a.get('tiktok_score'),
                instagram_score=a.get('instagram_score'),
                youtube_score=a.get('youtube_score'),
                modifications=mods
            )

            results.append(a)

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


def render_results(analyses, folder, prefix):
    """Afficher les resultats de generation"""
    if not analyses:
        return

    # Top bar: folder + ZIP + summary
    avg = sum(a['uniqueness'] for a in analyses) / len(analyses)
    safe = sum(1 for a in analyses if a['uniqueness'] >= 60)

    safe_analyses = [a for a in analyses if a['uniqueness'] >= 60]

    top1, top2, top3, top4 = st.columns([2, 1.5, 1, 1])
    with top1:
        st.markdown(f"<div class='folder-badge'>📁 {folder}/</div>", unsafe_allow_html=True)
    with top2:
        st.markdown(f"""<div style="background:#1C1C1E;border:1px solid #2C2C2E;border-radius:8px;padding:6px 10px;
            font-size:0.78rem;color:#86868B;text-align:center">
            📊 Moy. <b style="color:#F5F5F7">{avg:.0f}%</b> &nbsp; ✅ <b style="color:#30D158">{safe}/{len(analyses)}</b> safe
        </div>""", unsafe_allow_html=True)
    with top3:
        zip_all = build_zip_from_analyses(analyses)
        st.download_button("📦 Tout", zip_all,
                           file_name=f"{folder}.zip", mime="application/zip",
                           key=f"zip_{prefix}", use_container_width=True)
    with top4:
        if safe_analyses:
            zip_safe = build_zip_from_analyses(safe_analyses)
            st.download_button("🟢 Safe IG", zip_safe,
                               file_name=f"{folder}_safe_instagram.zip", mime="application/zip",
                               key=f"zipsafe_{prefix}", use_container_width=True)
        else:
            st.markdown('<div style="font-size:0.7rem;color:#FF453A;text-align:center;padding:8px">Aucune safe</div>', unsafe_allow_html=True)

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

    # Video preview gallery — 2 per row with individual download buttons
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("##### 🎬 Aperçus — verifier les modifications")
    preview_per_row = 4
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
                    with open(p, 'rb') as f:
                        st.download_button(f"⬇ {a['name']}", f.read(),
                                           file_name=f"{a['name']}.mp4", mime="video/mp4",
                                           key=f"dlprev_{prefix}_{start}_{i}", use_container_width=True)




# ============ MAIN ============

def main():
    st.markdown("""<div class="header-bar">
        <span class="header-logo">LTP</span>
        <span class="header-title">TikFusion</span>
    </div>""", unsafe_allow_html=True)

    tab_single, tab_bulk, tab_farm, tab_stats, tab_config = st.tabs([
        "📤 Single", "📦 Bulk", "🏭 Ferme",
        "📊 Stats", "⚙️ Config"
    ])

    # ===== CONFIGURATION (first for variables) =====
    with tab_config:
        st.markdown("### ⚙️ Configuration")

        # FFmpeg diagnostic
        ok, ffpath, info = _check_ffmpeg()
        if ok:
            st.markdown(f"""<div style="background:#0A2F1C;border:1px solid #30D158;border-radius:8px;padding:8px 12px;font-size:0.78rem;color:#30D158;margin-bottom:12px">
                ✅ FFmpeg OK — <code>{ffpath}</code><br><span style="font-size:0.7rem;color:#86868B">{info[:80]}</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="background:#2D1215;border:1px solid #FF453A;border-radius:8px;padding:8px 12px;font-size:0.78rem;color:#FF453A;margin-bottom:12px">
                ❌ FFmpeg non disponible — <code>{ffpath}</code><br><span style="font-size:0.7rem">{info[:120]}</span>
            </div>""", unsafe_allow_html=True)

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
        # Dynamic score preview using the same formula as actual generation
        from uniquifier import INTENSITY_PRESETS
        _preset = INTENSITY_PRESETS.get(intensity, INTENSITY_PRESETS["medium"])
        _typical = {
            "noise": _preset["noise_strength"] * 0.7 if mod_noise else 0,
            "zoom": (_preset["zoom_range"][0] + _preset["zoom_range"][1]) / 2 if mod_zoom else 1.0,
            "gamma": 1.015 if mod_gamma else 1.0,
            "hue_shift": _preset["color_shift"] // 2 if mod_hue else 0,
            "hflip": mod_hflip and _preset["hflip_chance"] >= 0.4,
            "crop_percent": _preset["crop_percent"] * 0.7 if mod_crop else 0,
            "speed": (_preset["speed_range"][0] + _preset["speed_range"][1]) / 2 if mod_speed else 1.0,
            "pitch_semitones": _preset["pitch_semitones"] * 0.7 if mod_pitch else 0,
            "fps": 30 + _preset["fps_shift"] * 0.7 if mod_fps else 30,
            "metadata_randomized": mod_meta,
        }
        _preview = estimate_uniqueness(_typical)
        ps = _preview['uniqueness']
        # Build detail breakdown
        d = []
        if mod_noise: d.append(f"📡+{min(round(_typical['noise'] * 3), 18)}")
        if mod_zoom: d.append(f"🔍+{min(round((_typical['zoom'] - 1.0) * 350), 14)}")
        if mod_gamma: d.append(f"🌗+{min(round(abs(_typical['gamma'] - 1.0) * 200), 5)}")
        if mod_hue: d.append(f"🎨+{min(round(abs(_typical['hue_shift']) * 0.15), 2)}")
        if mod_hflip and _typical['hflip']: d.append("🪞+12")
        if mod_crop: d.append(f"✂️+{min(round(_typical['crop_percent'] * 2), 4)}")
        if mod_speed: d.append(f"🔄+{min(round(abs(_typical['speed'] - 1.0) * 40), 3)}")
        if mod_pitch: d.append(f"🎵+{min(round(abs(_typical['pitch_semitones']) * 35), 20)}")
        if mod_fps: d.append(f"🎞️+{min(round(abs(_typical['fps'] - 30) * 50), 5)}")
        d.append("🔊+3")
        if mod_meta: d.append("🏷️+5")
        d.append("💾+8")
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
        st.markdown("### 🔍 Comment fonctionne la detection Instagram")
        st.markdown("""<div class="info-card">
            <h4>🔍 Comment fonctionne la detection Instagram</h4>
            <p>Instagram utilise <span class="highlight">3 couches de detection</span> pour reperer les videos dupliquees :</p>
            <div class="step">
                <b>1. Perceptual Hashing (~35%)</b> — Compare l'empreinte visuelle de chaque frame. Le miroir, le zoom, le bruit pixel et le crop cassent ce hash.<br>
                <b>2. Deep Learning (~30%)</b> — Un modele IA analyse le contenu semantique. Le changement de vitesse, le crop et la combinaison de mods le trompent.<br>
                <b>3. Audio Fingerprinting (~25%)</b> — Compare l'empreinte audio. Le pitch shift et le changement de FPS suffisent a passer.<br>
                <b>4. Metadata Check (~10%)</b> — Verifie les metadonnees du fichier. La randomisation des metadata regle ca.
            </div>
            <p style="margin-top:10px"><span class="highlight">Score >= 60% = Safe Instagram.</span> Toutes les modifications sont appliquees automatiquement par TikFusion.</p>
        </div>""", unsafe_allow_html=True)

    # Config values
    output_dir = st.session_state.get('cfg_output', 'outputs')
    intensity = st.session_state.get('cfg_intensity', 'medium')
    enabled_mods = {k: st.session_state.get(f"mod_{k}", True)
                    for k in ["noise","zoom","gamma","hue","hflip","crop","speed","pitch","fps","meta"]}

    # ===== SINGLE =====
    with tab_single:
        col_l, col_r = st.columns([1, 4])

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
                        stat.empty(); prog.empty()
                        if analyses:
                            st.session_state['single_analyses'] = analyses
                            st.session_state['single_folder'] = folder
                            st.success(f"✅ {len(analyses)} variations generees")
                        elif folder != "error":
                            st.error("❌ Toutes les variations ont echoue. Verifie l'onglet Config pour le diagnostic FFmpeg.")
                    except Exception as e:
                        stat.empty(); prog.empty()
                        st.error(f"❌ Erreur: {e}")
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
                    "single"
                )

    # ===== BULK =====
    with tab_bulk:
        col_l, col_r = st.columns([1, 4])

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
                        from uniquifier import uniquify_video_ffmpeg, FFMPEG_BIN
                        ok, ffpath, info = _check_ffmpeg()
                        if not ok:
                            st.error(f"FFmpeg non disponible ({ffpath}): {info}")
                            st.info("Installe `imageio-ffmpeg` (pip) ou `ffmpeg` (systeme).")
                            raise RuntimeError("FFmpeg unavailable")
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
                        stat.empty(); prog.empty()
                        total_gen = sum(r['success_count'] for r in all_res)
                        if total_gen > 0:
                            st.success(f"✅ {total_gen} videos generees")
                        else:
                            st.error("❌ Generation echouee — verifie que ffmpeg est installe")
                    except Exception as e:
                        stat.empty(); prog.empty()
                        st.error(f"❌ Erreur: {e}")

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

                # === 2 ZIP BUTTONS ===
                z1, z2 = st.columns(2)
                with z1:
                    zip_all = build_zip_from_bulk_results(results, filter_safe=False)
                    st.download_button("📦 Tout telecharger (ZIP)", zip_all,
                                       file_name=f"{bf}.zip", mime="application/zip",
                                       key="zip_bulk", use_container_width=True)
                with z2:
                    if safe > 0:
                        zip_safe = build_zip_from_bulk_results(results, filter_safe=True)
                        st.download_button(f"🟢 Safe Instagram ({safe} videos)", zip_safe,
                                           file_name=f"{bf}_safe_instagram.zip", mime="application/zip",
                                           key="zipsafe_bulk", use_container_width=True)
                    else:
                        st.markdown('<div style="background:#1C1C1E;border:1px solid #FF453A;border-radius:8px;padding:8px;text-align:center;font-size:0.78rem;color:#FF453A">Aucune variation safe Instagram</div>', unsafe_allow_html=True)

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
                        pcols = st.columns(min(4, max(1, len(r['variations']))))
                        for i, v in enumerate(r['variations']):
                            p = v.get('output_path','')
                            if p and os.path.exists(p):
                                with pcols[i % 4]:
                                    st.video(p)
                                    u = v['uniqueness']
                                    bc, _ = get_badge(u)
                                    st.markdown(f'<div style="text-align:center;margin-top:-6px;font-size:.75rem;color:#86868B">{v["name"]} <span class="{bc}" style="font-size:.68rem;padding:1px 6px">{u:.0f}%</span></div>', unsafe_allow_html=True)

            else:
                st.info("👈 Upload plusieurs videos et lance le traitement")

    # ===== FERME (Farm Mode) =====
    with tab_farm:
        st.markdown("### 🏭 Mode Ferme — Traitement en masse")
        st.markdown('<div style="color:#86868B;font-size:0.82rem;margin-bottom:12px">Traitement en masse — upload tes videos et lance la generation. <b>Garde cette page ouverte</b> pendant toute la duree du traitement.</div>', unsafe_allow_html=True)
        st.warning("⚠️ Ne ferme pas le navigateur pendant le traitement. La generation s'arrete si la connexion est coupee.")

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

                farm_vpv = st.slider("Variations par video", 1, 20, 5, key="farm_vpv")

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

                    # Check FFmpeg before starting Farm
                    ok, ffpath, info = _check_ffmpeg()
                    if not ok:
                        st.error(f"FFmpeg non disponible ({ffpath}): {info}")
                        st.info("Installe `imageio-ffmpeg` (pip) ou `ffmpeg` (systeme).")
                        st.session_state['farm_running'] = False
                        st.rerun()

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

                        for j in range(farm_vpv):
                            status_text.markdown(f"""<div style="background:#1C1C1E;border:1px solid #2C2C2E;
                                border-radius:8px;padding:8px 12px;font-size:0.85rem;color:#F5F5F7">
                                ⏳ <b>[{vi+1}/{total_videos}]</b> {video_name} — V{j+1:02d}/{farm_vpv}
                            </div>""", unsafe_allow_html=True)

                            out = os.path.join(video_folder, f"V{j+1:02d}.mp4")
                            r = uniquify_video_ffmpeg(vpath, out, intensity, enabled_mods)

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

                # === 2 ZIP BUTTONS ===
                z1, z2 = st.columns(2)
                with z1:
                    zip_all = build_zip_from_bulk_results(results, filter_safe=False)
                    st.download_button("📦 Tout telecharger (ZIP)", zip_all,
                                       file_name=f"{farm_folder}.zip", mime="application/zip",
                                       key="zip_farm", use_container_width=True)
                with z2:
                    if safe > 0:
                        zip_safe = build_zip_from_bulk_results(results, filter_safe=True)
                        st.download_button(f"🟢 Safe Instagram ({safe} videos)", zip_safe,
                                           file_name=f"{farm_folder}_safe_instagram.zip", mime="application/zip",
                                           key="zipsafe_farm", use_container_width=True)
                    else:
                        st.markdown('<div style="background:#1C1C1E;border:1px solid #FF453A;border-radius:8px;padding:8px;text-align:center;font-size:0.78rem;color:#FF453A">Aucune variation safe Instagram</div>', unsafe_allow_html=True)

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
                            pcols = st.columns(min(4, len(r['variations'])))
                            for i, v in enumerate(r['variations']):
                                p = v.get('output_path','')
                                if p and os.path.exists(p):
                                    with pcols[i % 4]:
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


    # ===== STATS =====
    with tab_stats:
        st.markdown("### 📊 Statistiques")

        # ---- Disk stats (always available) ----
        if os.path.exists(output_dir):
            vids = list(Path(output_dir).rglob("*.mp4"))
            folders = [f for f in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, f))]
            sz = sum(f.stat().st_size for f in vids) / (1024*1024)
            dc1, dc2, dc3 = st.columns(3)
            dc1.metric("📁 Dossiers", len(folders))
            dc2.metric("📹 Videos sur disque", len(vids))
            dc3.metric("💾 Espace utilise", f"{sz:.1f} MB")
        else:
            st.info("Aucun dossier de sortie detecte.")

        st.markdown("---")

        # ---- SQLite analytics ----
        analytics = get_analytics()

        # KPI row
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Sessions totales", analytics.get("total_sessions", 0))
        k2.metric("Variations generees", analytics.get("total_variations", 0))
        k3.metric("Score moyen", f"{analytics.get('avg_uniqueness', 0)}%")
        k4.metric("Variations safe (>=60%)", analytics.get("safe_count", 0))
        total_vars = analytics.get("total_variations", 0)
        safe_rate = round(analytics["safe_count"] / total_vars * 100) if total_vars else 0
        k5.metric("Taux safe", f"{safe_rate}%")

        st.markdown("---")

        # ---- Charts row ----
        chart_left, chart_right = st.columns(2)

        # Score distribution bar chart
        with chart_left:
            st.markdown("#### Distribution des scores d'unicite")
            score_dist = analytics.get("score_distribution", {})
            if score_dist:
                buckets_order = ["0-19", "20-39", "40-59", "60-79", "80-100"]
                chart_data = {b: score_dist.get(b, 0) for b in buckets_order}
                st.bar_chart(chart_data)
            else:
                st.caption("Aucune variation enregistree.")

        # Sessions by mode pie-like display
        with chart_right:
            st.markdown("#### Sessions par mode")
            modes = analytics.get("sessions_by_mode", {})
            if modes:
                for mode_name, cnt in sorted(modes.items(), key=lambda x: -x[1]):
                    pct = round(cnt / analytics["total_sessions"] * 100) if analytics["total_sessions"] else 0
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
                        <div style="flex:1;background:#2A2A2E;border-radius:6px;overflow:hidden;height:24px">
                            <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#66cc8a,#30D158);border-radius:6px;
                                        display:flex;align-items:center;padding-left:8px;font-size:12px;color:#fff;font-weight:600">
                                {mode_name}
                            </div>
                        </div>
                        <span style="color:#8E8E93;font-size:13px;min-width:60px;text-align:right">{cnt} ({pct}%)</span>
                    </div>""", unsafe_allow_html=True)
            else:
                st.caption("Aucune session enregistree.")

        st.markdown("---")

        # ---- Platform scores ----
        st.markdown("#### Scores moyens par plateforme")
        plat1, plat2, plat3 = st.columns(3)
        avg_tk = analytics.get("avg_tiktok")
        avg_ig = analytics.get("avg_instagram")
        avg_yt = analytics.get("avg_youtube")
        plat1.markdown(f"""
        <div style="background:#1A1A1E;border:1px solid #FF004F;border-radius:12px;padding:20px;text-align:center">
            <div style="font-size:28px">🎵</div>
            <div style="font-size:13px;color:#8E8E93;margin:4px 0">TikTok</div>
            <div style="font-size:24px;font-weight:700;color:#FF004F">{f'{avg_tk:.0f}%' if avg_tk else '—'}</div>
        </div>""", unsafe_allow_html=True)
        plat2.markdown(f"""
        <div style="background:#1A1A1E;border:1px solid #E1306C;border-radius:12px;padding:20px;text-align:center">
            <div style="font-size:28px">📸</div>
            <div style="font-size:13px;color:#8E8E93;margin:4px 0">Instagram</div>
            <div style="font-size:24px;font-weight:700;color:#E1306C">{f'{avg_ig:.0f}%' if avg_ig else '—'}</div>
        </div>""", unsafe_allow_html=True)
        plat3.markdown(f"""
        <div style="background:#1A1A1E;border:1px solid #FF0000;border-radius:12px;padding:20px;text-align:center">
            <div style="font-size:28px">▶️</div>
            <div style="font-size:13px;color:#8E8E93;margin:4px 0">YouTube</div>
            <div style="font-size:24px;font-weight:700;color:#FF0000">{f'{avg_yt:.0f}%' if avg_yt else '—'}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")

        # ---- Modification effectiveness ----
        st.markdown("#### Modifications les plus efficaces (variations >=70%)")
        mod_samples = analytics.get("high_score_mod_samples", [])
        if mod_samples:
            mod_counts = {}
            for mods in mod_samples:
                if isinstance(mods, list):
                    for m in mods:
                        name = m if isinstance(m, str) else m.get("name", str(m))
                        mod_counts[name] = mod_counts.get(name, 0) + 1
                elif isinstance(mods, dict):
                    for k in mods:
                        mod_counts[k] = mod_counts.get(k, 0) + 1
            if mod_counts:
                sorted_mods = sorted(mod_counts.items(), key=lambda x: -x[1])
                for mod_name, count in sorted_mods:
                    pct = round(count / len(mod_samples) * 100)
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
                        <code style="min-width:120px;color:#66cc8a">{mod_name}</code>
                        <div style="flex:1;background:#2A2A2E;border-radius:4px;overflow:hidden;height:18px">
                            <div style="width:{pct}%;height:100%;background:#66cc8a;border-radius:4px"></div>
                        </div>
                        <span style="color:#8E8E93;font-size:12px;min-width:70px;text-align:right">{count}x ({pct}%)</span>
                    </div>""", unsafe_allow_html=True)
            else:
                st.caption("Pas assez de donnees.")
        else:
            st.caption("Aucune variation avec score >=70% enregistree.")

        st.markdown("---")

        # ---- Recent sessions ----
        st.markdown("#### Dernieres sessions")
        recent = analytics.get("recent_sessions", [])
        if recent:
            for sess in recent:
                mode_badge = sess.get("mode", "?")
                created = sess.get("created_at", "")[:16]
                src_url = sess.get("source_url", "")
                vs = sess.get("virality_score")
                n_var = sess.get("num_variations", 0)
                intensity = sess.get("intensity", "")
                vs_str = f" | Viralite: {vs:.0f}%" if vs else ""
                url_str = f" | {src_url[:40]}..." if src_url and len(src_url) > 40 else (f" | {src_url}" if src_url else "")
                st.markdown(f"""
                <div style="background:#1A1A1E;border-radius:8px;padding:10px 14px;margin-bottom:6px;
                            display:flex;align-items:center;gap:12px;border-left:3px solid #66cc8a">
                    <span style="background:#66cc8a22;color:#66cc8a;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600">
                        {mode_badge}
                    </span>
                    <span style="color:#F5F5F7;font-size:13px;flex:1">
                        {n_var} variations | {intensity}{vs_str}{url_str}
                    </span>
                    <span style="color:#636366;font-size:11px">{created}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("Aucune session enregistree.")

        # ---- Folder breakdown (preserved from original) ----
        if os.path.exists(output_dir):
            st.markdown("---")
            st.markdown("#### Arborescence des dossiers")
            folders = [f for f in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, f))]
            farm_folders = [f for f in sorted(folders, reverse=True) if "FERME" in f]
            bulk_folders = [f for f in sorted(folders, reverse=True) if "BULK" in f]
            other_folders = [f for f in sorted(folders, reverse=True) if "FERME" not in f and "BULK" not in f]

            if farm_folders:
                st.markdown("**🏭 Ferme**")
                for f in farm_folders:
                    n = len(list(Path(os.path.join(output_dir, f)).rglob("*.mp4")))
                    st.text(f"  📁 {f} — {n} videos")
            if bulk_folders:
                st.markdown("**📦 Bulk**")
                for f in bulk_folders:
                    n = len(list(Path(os.path.join(output_dir, f)).rglob("*.mp4")))
                    st.text(f"  📁 {f} — {n} videos")
            if other_folders:
                st.markdown("**📤 Single / Import**")
                for f in other_folders:
                    n = len(list(Path(os.path.join(output_dir, f)).rglob("*.mp4")))
                    st.text(f"  📁 {f} — {n} videos")


if __name__ == "__main__":
    main()
