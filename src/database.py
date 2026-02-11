"""
TikFusion — SQLite persistence layer
Stores sessions, variations, publications, results for analytics.
"""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tikfusion.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        mode TEXT NOT NULL,
        source_url TEXT,
        source_platform TEXT,
        virality_score REAL,
        folder_name TEXT,
        num_variations INTEGER DEFAULT 0,
        intensity TEXT DEFAULT 'medium'
    );

    CREATE TABLE IF NOT EXISTS variations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        output_path TEXT,
        uniqueness_score REAL,
        tiktok_score REAL,
        instagram_score REAL,
        youtube_score REAL,
        modifications_json TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS publications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        variation_id INTEGER,
        post_id TEXT,
        caption TEXT,
        account_ids_json TEXT,
        platforms_json TEXT,
        status TEXT DEFAULT 'processing',
        scheduled_at TEXT,
        published_at TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (variation_id) REFERENCES variations(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS pub_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        publication_id INTEGER NOT NULL,
        social_account_id INTEGER,
        platform TEXT,
        success INTEGER DEFAULT 0,
        post_url TEXT,
        platform_post_id TEXT,
        username TEXT,
        error_json TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (publication_id) REFERENCES publications(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()


# ---- Sessions ----

def save_session(mode, source_url=None, source_platform=None,
                 virality_score=None, folder_name=None,
                 num_variations=0, intensity="medium"):
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO sessions (mode, source_url, source_platform, virality_score,
           folder_name, num_variations, intensity)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (mode, source_url, source_platform, virality_score,
         folder_name, num_variations, intensity)
    )
    sid = cur.lastrowid
    conn.commit()
    conn.close()
    return sid


def get_sessions(limit=50, mode=None):
    conn = get_db()
    if mode:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE mode=? ORDER BY created_at DESC LIMIT ?",
            (mode, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session(session_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ---- Variations ----

def save_variation(session_id, name, output_path, uniqueness_score,
                   tiktok_score=None, instagram_score=None, youtube_score=None,
                   modifications=None):
    conn = get_db()
    mods_json = json.dumps(modifications) if modifications else None
    cur = conn.execute(
        """INSERT INTO variations (session_id, name, output_path, uniqueness_score,
           tiktok_score, instagram_score, youtube_score, modifications_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (session_id, name, output_path, uniqueness_score,
         tiktok_score, instagram_score, youtube_score, mods_json)
    )
    vid = cur.lastrowid
    conn.commit()
    conn.close()
    return vid


def get_session_variations(session_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM variations WHERE session_id=? ORDER BY name", (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---- Publications ----

def save_publication(post_id, caption, account_ids, platforms,
                     variation_id=None, status="processing",
                     scheduled_at=None):
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO publications (variation_id, post_id, caption, account_ids_json,
           platforms_json, status, scheduled_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (variation_id, post_id, caption,
         json.dumps(account_ids), json.dumps(platforms),
         status, scheduled_at)
    )
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return pid


def update_publication_status(publication_id, status, published_at=None):
    conn = get_db()
    if published_at:
        conn.execute(
            "UPDATE publications SET status=?, published_at=? WHERE id=?",
            (status, published_at, publication_id)
        )
    else:
        conn.execute(
            "UPDATE publications SET status=? WHERE id=?", (status, publication_id)
        )
    conn.commit()
    conn.close()


def get_publications(limit=50, status=None):
    conn = get_db()
    if status:
        rows = conn.execute(
            "SELECT * FROM publications WHERE status=? ORDER BY created_at DESC LIMIT ?",
            (status, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM publications ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---- Publication Results ----

def save_pub_result(publication_id, social_account_id, platform,
                    success, post_url=None, platform_post_id=None,
                    username=None, error=None):
    conn = get_db()
    conn.execute(
        """INSERT INTO pub_results (publication_id, social_account_id, platform,
           success, post_url, platform_post_id, username, error_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (publication_id, social_account_id, platform, int(success),
         post_url, platform_post_id, username,
         json.dumps(error) if error else None)
    )
    conn.commit()
    conn.close()


# ---- Analytics ----

def get_analytics():
    conn = get_db()
    stats = {}

    # Total sessions
    stats['total_sessions'] = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

    # Total variations
    stats['total_variations'] = conn.execute("SELECT COUNT(*) FROM variations").fetchone()[0]

    # Average uniqueness score
    row = conn.execute("SELECT AVG(uniqueness_score) FROM variations WHERE uniqueness_score IS NOT NULL").fetchone()
    stats['avg_uniqueness'] = round(row[0], 1) if row[0] else 0

    # Safe count (>=60)
    stats['safe_count'] = conn.execute(
        "SELECT COUNT(*) FROM variations WHERE uniqueness_score >= 60"
    ).fetchone()[0]

    # Total publications
    stats['total_publications'] = conn.execute("SELECT COUNT(*) FROM publications").fetchone()[0]

    # Successful publications
    stats['successful_publications'] = conn.execute(
        "SELECT COUNT(*) FROM pub_results WHERE success=1"
    ).fetchone()[0]

    # Failed publications
    stats['failed_publications'] = conn.execute(
        "SELECT COUNT(*) FROM pub_results WHERE success=0"
    ).fetchone()[0]

    # Publications by status
    for s in ['posted', 'scheduled', 'processing']:
        stats[f'pub_{s}'] = conn.execute(
            "SELECT COUNT(*) FROM publications WHERE status=?", (s,)
        ).fetchone()[0]

    # Sessions by mode
    modes = conn.execute(
        "SELECT mode, COUNT(*) as cnt FROM sessions GROUP BY mode ORDER BY cnt DESC"
    ).fetchall()
    stats['sessions_by_mode'] = {r['mode']: r['cnt'] for r in modes}

    # Score distribution
    buckets = conn.execute("""
        SELECT
            CASE
                WHEN uniqueness_score >= 80 THEN '80-100'
                WHEN uniqueness_score >= 60 THEN '60-79'
                WHEN uniqueness_score >= 40 THEN '40-59'
                WHEN uniqueness_score >= 20 THEN '20-39'
                ELSE '0-19'
            END as bucket,
            COUNT(*) as cnt
        FROM variations WHERE uniqueness_score IS NOT NULL
        GROUP BY bucket ORDER BY bucket DESC
    """).fetchall()
    stats['score_distribution'] = {r['bucket']: r['cnt'] for r in buckets}

    # Average scores by platform
    row = conn.execute("""
        SELECT AVG(tiktok_score), AVG(instagram_score), AVG(youtube_score)
        FROM variations
        WHERE tiktok_score IS NOT NULL
    """).fetchone()
    stats['avg_tiktok'] = round(row[0], 1) if row[0] else None
    stats['avg_instagram'] = round(row[1], 1) if row[1] else None
    stats['avg_youtube'] = round(row[2], 1) if row[2] else None

    # Recent sessions (last 10)
    stats['recent_sessions'] = [dict(r) for r in conn.execute(
        "SELECT * FROM sessions ORDER BY created_at DESC LIMIT 10"
    ).fetchall()]

    # Modification effectiveness (which mods are used in high-score variations)
    high_score_mods = conn.execute("""
        SELECT modifications_json FROM variations
        WHERE uniqueness_score >= 70 AND modifications_json IS NOT NULL
        ORDER BY uniqueness_score DESC LIMIT 50
    """).fetchall()
    stats['high_score_mod_samples'] = [json.loads(r[0]) for r in high_score_mods if r[0]]

    # Publications timeline (last 30 days)
    stats['pub_timeline'] = [dict(r) for r in conn.execute("""
        SELECT DATE(created_at) as day, COUNT(*) as cnt, status
        FROM publications
        WHERE created_at >= datetime('now', '-30 days')
        GROUP BY day, status
        ORDER BY day
    """).fetchall()]

    conn.close()
    return stats


# Initialize on import
init_db()
