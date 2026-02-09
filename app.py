"""
TikFusion MVP - Interface compacte
"""
import streamlit as st
import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

st.set_page_config(page_title="TikFusion MVP", page_icon="🎬", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; background: linear-gradient(90deg, #ff0050, #00f2ea); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .folder-name { background: #333; color: #00f2ea; padding: 10px; border-radius: 5px; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

def compare_to_original(original_path, variation_path):
    """Compare une variation à l'original"""
    try:
        from uniqueness_checker import UniquenessChecker
        checker = UniquenessChecker()
        result = checker.compare_videos(original_path, variation_path)
        similarity = result['similarity_percent']
        uniqueness = 100 - similarity
        return {
            'similarity': similarity,
            'uniqueness': uniqueness,
        }
    except:
        return {'uniqueness': 50}

def get_dated_folder_name():
    """Génère un nom de dossier avec date et heure"""
    now = datetime.now()
    mois_fr = {1: "janvier", 2: "fevrier", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
               7: "juillet", 8: "aout", 9: "septembre", 10: "octobre", 11: "novembre", 12: "decembre"}
    return f"{now.day} {mois_fr[now.month]} {now.strftime('%Hh%M')}"

def format_modifications(mods):
    """Formate les modifications en tags visuels compacts"""
    tags = []
    if mods.get("hflip"):
        tags.append('<span style="background:#f44336;color:white;padding:2px 6px;border-radius:3px;font-size:0.8em">🪞 Miroir</span>')
    speed = mods.get("speed", 1.0)
    if abs(speed - 1.0) > 0.005:
        tags.append(f'<span style="background:#333;color:#00f2ea;padding:2px 6px;border-radius:3px;font-size:0.8em">🔄 x{speed:.2f}</span>')
    hue = mods.get("hue_shift", 0)
    if abs(hue) > 0:
        tags.append(f'<span style="background:#333;color:#ff9800;padding:2px 6px;border-radius:3px;font-size:0.8em">🎨 {hue:+d}°</span>')
    crop = mods.get("crop_percent", 0)
    if crop > 0.1:
        tags.append(f'<span style="background:#333;color:#8bc34a;padding:2px 6px;border-radius:3px;font-size:0.8em">✂️ {crop:.1f}%</span>')
    if mods.get("metadata_randomized"):
        tags.append('<span style="background:#333;color:#9c27b0;padding:2px 6px;border-radius:3px;font-size:0.8em">🏷️ Metadata</span>')
    return " ".join(tags) if tags else '<span style="color:#666;font-size:0.8em">-</span>'

def main():
    st.markdown('<p class="main-header">🎬 TikFusion MVP</p>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ Configuration")
        output_dir = st.text_input("📁 Dossier racine", value="outputs")
        intensity = st.select_slider("🎚️ Intensité", options=["low", "medium", "high"], value="medium")

        st.markdown("---")
        st.markdown("**📁 Dossiers récents:**")
        if os.path.exists(output_dir):
            folders = sorted([f for f in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, f))], reverse=True)
            for folder in folders[:5]:
                count = len(list(Path(os.path.join(output_dir, folder)).rglob("*.mp4")))
                st.text(f"📁 {folder} ({count} vidéos)")

    # TABS
    tab1, tab2, tab3 = st.tabs(["📤 Single Upload", "📦 Bulk Upload", "📊 Stats"])

    # ========== TAB 1: SINGLE UPLOAD ==========
    with tab1:
        st.header("📤 Upload unique")

        col1, col2 = st.columns([1, 2])

        with col1:
            uploaded = st.file_uploader("📹 Ta vidéo", type=['mp4', 'mov', 'avi'], key="single")

            if uploaded:
                st.video(uploaded)
                num_vars = st.slider("Variations", 1, 15, 5, key="single_vars")

                if st.button("🚀 Générer", type="primary", key="single_btn"):
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                        tmp.write(uploaded.read())
                        original_path = tmp.name

                    progress = st.progress(0)
                    status = st.empty()

                    try:
                        from uniquifier import batch_uniquify

                        status.text("⏳ Génération...")
                        results = batch_uniquify(original_path, output_dir, num_vars, intensity)

                        folder_name = os.path.basename(os.path.dirname(results[0]["output_path"])) if results else ""

                        status.text("🔍 Analyse...")
                        analyses = []
                        for i, r in enumerate(results):
                            if r["success"]:
                                analysis = compare_to_original(original_path, r["output_path"])
                                analysis['name'] = Path(r["output_path"]).stem
                                analysis['modifications'] = r.get("modifications", {})
                                analysis['output_path'] = r["output_path"]
                                analyses.append(analysis)
                            progress.progress((i + 1) / len(results))

                        st.session_state['single_analyses'] = analyses
                        st.session_state['single_folder'] = folder_name
                        status.empty()
                        st.success(f"✅ {len(analyses)} variations générées!")

                        os.unlink(original_path)
                    except Exception as e:
                        st.error(f"Erreur: {e}")

        with col2:
            if 'single_analyses' in st.session_state:
                analyses = st.session_state['single_analyses']
                st.markdown(f"**📁 outputs/{st.session_state.get('single_folder', '')}/")

                st.markdown("""<div style="background:#1a1a2e;padding:8px 12px;border-radius:6px;margin-bottom:12px;font-size:0.85em">
                🟢 ≥ 80% = Suffisamment unique &nbsp;|&nbsp; 🔴 < 80% = Trop similaire à l'original
                </div>""", unsafe_allow_html=True)

                for a in analyses:
                    cols = st.columns([1, 3, 1, 2, 1])
                    # Nom
                    cols[0].markdown(f"**{a['name']}**")
                    # Tags modifications
                    cols[1].markdown(format_modifications(a.get('modifications', {})), unsafe_allow_html=True)
                    # Unicité vert/rouge
                    u = a['uniqueness']
                    color = '#00c853' if u >= 80 else '#f44336'
                    cols[2].markdown(f"<span style='background:{color};color:white;padding:4px 8px;border-radius:5px;font-weight:bold'>{u:.0f}%</span>", unsafe_allow_html=True)
                    # Preview vidéo
                    output_path = a.get('output_path', '')
                    if output_path and os.path.exists(output_path):
                        cols[3].video(output_path)
                        # Download
                        with open(output_path, "rb") as f:
                            cols[4].download_button(
                                "⬇️",
                                f.read(),
                                file_name=Path(output_path).name,
                                mime="video/mp4",
                                key=f"dl_{a['name']}"
                            )

    # ========== TAB 2: BULK UPLOAD ==========
    with tab2:
        st.header("📦 Bulk Upload - Traitement en masse")
        st.markdown("Upload jusqu'à **10 vidéos** et génère des variations pour chacune.")

        col1, col2 = st.columns([1, 1])

        with col1:
            uploaded_files = st.file_uploader(
                "📹 Sélectionne plusieurs vidéos",
                type=['mp4', 'mov', 'avi'],
                accept_multiple_files=True,
                key="bulk"
            )

            if uploaded_files:
                if len(uploaded_files) > 10:
                    st.warning(f"⚠️ Maximum 10 vidéos. Seules les 10 premières seront traitées.")
                    uploaded_files = uploaded_files[:10]
                st.success(f"📁 {len(uploaded_files)} vidéos sélectionnées")

                for f in uploaded_files[:5]:
                    st.text(f"  📹 {f.name}")
                if len(uploaded_files) > 5:
                    st.text(f"  ... +{len(uploaded_files) - 5} autres")

                vars_per_video = st.slider("Variations par vidéo", 1, 10, 3, key="bulk_vars")

                total = len(uploaded_files) * vars_per_video
                st.warning(f"⚠️ Total: **{total} vidéos** seront générées")

                if st.button("🚀 Lancer le Bulk Processing", type="primary", key="bulk_btn"):

                    # Create main folder for this bulk session
                    bulk_folder = get_dated_folder_name() + " - BULK"
                    bulk_path = os.path.join(output_dir, bulk_folder)
                    os.makedirs(bulk_path, exist_ok=True)

                    overall_progress = st.progress(0)
                    status = st.empty()

                    all_results = []

                    try:
                        from uniquifier import uniquify_video_ffmpeg

                        for vid_idx, uploaded_file in enumerate(uploaded_files):
                            video_name = Path(uploaded_file.name).stem
                            status.text(f"⏳ [{vid_idx + 1}/{len(uploaded_files)}] Traitement: {video_name}")

                            # Save original temporarily
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                                tmp.write(uploaded_file.read())
                                original_path = tmp.name

                            # Create subfolder for this video
                            video_folder = os.path.join(bulk_path, video_name)
                            os.makedirs(video_folder, exist_ok=True)

                            video_results = {
                                'name': video_name,
                                'variations': [],
                                'success_count': 0
                            }

                            # Generate variations
                            for var_idx in range(vars_per_video):
                                output_path = os.path.join(video_folder, f"V{var_idx + 1:02d}.mp4")
                                result = uniquify_video_ffmpeg(original_path, output_path, intensity)

                                if result["success"]:
                                    analysis = compare_to_original(original_path, output_path)
                                    video_results['variations'].append({
                                        'name': f"V{var_idx + 1:02d}",
                                        'output_path': output_path,
                                        'uniqueness': analysis['uniqueness'],
                                        'modifications': result.get("modifications", {})
                                    })
                                    video_results['success_count'] += 1

                            all_results.append(video_results)
                            os.unlink(original_path)

                            overall_progress.progress((vid_idx + 1) / len(uploaded_files))

                        st.session_state['bulk_results'] = all_results
                        st.session_state['bulk_folder'] = bulk_folder
                        st.session_state['bulk_path'] = bulk_path

                        status.empty()
                        total_success = sum(r['success_count'] for r in all_results)
                        st.success(f"✅ Terminé! {total_success} vidéos générées!")

                    except Exception as e:
                        st.error(f"Erreur: {e}")

        with col2:
            st.subheader("📊 Résultats Bulk")

            if 'bulk_results' in st.session_state:
                results = st.session_state['bulk_results']
                bulk_folder = st.session_state.get('bulk_folder', '')
                bulk_path = st.session_state.get('bulk_path', '')

                st.markdown(f"<div class='folder-name'>📁 outputs/{bulk_folder}/</div>", unsafe_allow_html=True)
                st.markdown("")

                # Summary stats
                total_videos = sum(r['success_count'] for r in results)
                all_variations = [v for r in results for v in r['variations']]
                avg_uniqueness = sum(v['uniqueness'] for v in all_variations) / len(all_variations) if all_variations else 0
                safe_count = sum(1 for v in all_variations if v['uniqueness'] >= 80)

                col_a, col_b, col_c = st.columns(3)
                col_a.metric("📹 Total", total_videos)
                col_b.metric("📊 Unicité moy.", f"{avg_uniqueness:.0f}%")
                col_c.metric("✅ Safe (≥80%)", f"{safe_count}/{len(all_variations)}")

                st.markdown("""<div style="background:#1a1a2e;padding:6px 10px;border-radius:5px;margin:8px 0;font-size:0.8em">
                🟢 ≥ 80% = Suffisamment unique &nbsp;|&nbsp; 🔴 < 80% = Trop similaire
                </div>""", unsafe_allow_html=True)

                # Per-video results
                for r in results:
                    with st.expander(f"📹 {r['name']} ({r['success_count']} variations)"):
                        if r['variations']:
                            for v in r['variations']:
                                cols = st.columns([1, 3, 1, 2, 1])
                                # Nom
                                cols[0].markdown(f"**{v['name']}**")
                                # Tags modifications
                                cols[1].markdown(format_modifications(v.get('modifications', {})), unsafe_allow_html=True)
                                # Unicité vert/rouge
                                u = v['uniqueness']
                                color = '#00c853' if u >= 80 else '#f44336'
                                cols[2].markdown(f"<span style='background:{color};color:white;padding:4px 8px;border-radius:5px;font-weight:bold'>{u:.0f}%</span>", unsafe_allow_html=True)
                                # Preview vidéo
                                vpath = v.get('output_path', '')
                                if vpath and os.path.exists(vpath):
                                    cols[3].video(vpath)
                                    # Download
                                    with open(vpath, "rb") as f:
                                        cols[4].download_button(
                                            "⬇️",
                                            f.read(),
                                            file_name=f"{r['name']}_{v['name']}.mp4",
                                            mime="video/mp4",
                                            key=f"dl_bulk_{r['name']}_{v['name']}"
                                        )
            else:
                st.info("👈 Upload plusieurs vidéos et lance le bulk processing")

                st.markdown("""
                ### 📁 Structure des fichiers
```
                outputs/
                └── 29 janvier 14h34 - BULK/
                    ├── video1/
                    │   ├── V01.mp4
                    │   ├── V02.mp4
                    │   └── V05.mp4
                    ├── video2/
                    │   ├── V01.mp4
                    │   └── ...
                    └── video3/
                        └── ...
```
                """)

    # ========== TAB 3: STATS ==========
    with tab3:
        st.header("📊 Statistiques globales")

        if os.path.exists(output_dir):
            all_videos = list(Path(output_dir).rglob("*.mp4"))
            all_folders = [f for f in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, f))]
            total_size = sum(f.stat().st_size for f in all_videos) / (1024 * 1024)

            col1, col2, col3 = st.columns(3)
            col1.metric("📁 Sessions", len(all_folders))
            col2.metric("📹 Total vidéos", len(all_videos))
            col3.metric("💾 Espace", f"{total_size:.1f} MB")

            st.markdown("---")
            st.markdown("### 📁 Toutes les sessions")

            for folder in sorted(all_folders, reverse=True):
                folder_path = os.path.join(output_dir, folder)
                videos = list(Path(folder_path).rglob("*.mp4"))
                st.text(f"📁 {folder} - {len(videos)} vidéos")

if __name__ == "__main__":
    main()
