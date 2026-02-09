"""
PostBridge API client — publish videos to TikTok, Instagram, YouTube, etc.
Handles: account listing, media upload, post creation, scheduling, results.
"""
import requests
import os

BASE_URL = "https://api.post-bridge.com/v1"

PLATFORM_ICONS = {
    "tiktok": "🎵",
    "instagram": "📸",
    "youtube": "▶️",
    "facebook": "📘",
    "twitter": "🐦",
    "linkedin": "💼",
    "pinterest": "📌",
    "threads": "🧵",
    "bluesky": "🦋",
}


def _headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _get(endpoint, api_key, params=None):
    r = requests.get(f"{BASE_URL}{endpoint}", headers=_headers(api_key), params=params or {}, timeout=15)
    r.raise_for_status()
    return r.json()


def _post(endpoint, api_key, json_data=None):
    r = requests.post(f"{BASE_URL}{endpoint}", headers=_headers(api_key), json=json_data or {}, timeout=30)
    r.raise_for_status()
    return r.json()


def list_accounts(api_key):
    """Récupère tous les comptes sociaux connectés."""
    accounts = []
    offset = 0
    while True:
        data = _get("/social-accounts", api_key, {"offset": offset, "limit": 50})
        items = data.get("data", [])
        accounts.extend(items)
        meta = data.get("meta", {})
        if not meta.get("next"):
            break
        offset += 50
    return accounts


def get_account_fields(api_key):
    """Debug: retourne les champs du premier compte pour inspection."""
    data = _get("/social-accounts", api_key, {"offset": 0, "limit": 1})
    items = data.get("data", [])
    if items:
        return items[0]
    return {}


def upload_video(api_key, video_path):
    """Upload une vidéo via signed URL. Retourne le media_id."""
    file_size = os.path.getsize(video_path)
    file_name = os.path.basename(video_path)

    # 1. Get signed upload URL
    resp = _post("/media/create-upload-url", api_key, {
        "name": file_name,
        "mime_type": "video/mp4",
        "size_bytes": file_size,
    })

    media_id = resp["media_id"]
    upload_url = resp["upload_url"]

    # 2. PUT file to signed URL
    with open(video_path, "rb") as f:
        put_resp = requests.put(
            upload_url,
            data=f,
            headers={"Content-Type": "video/mp4"},
            timeout=300,
        )
        put_resp.raise_for_status()

    return media_id


def create_post(api_key, caption, media_ids, account_ids,
                scheduled_at=None, platform_configs=None):
    """Crée un post (publication immédiate ou programmée).

    Args:
        api_key: PostBridge API key
        caption: Texte principal du post
        media_ids: Liste de media_id (vidéos uploadées)
        account_ids: Liste d'IDs de comptes sociaux
        scheduled_at: ISO 8601 datetime string pour programmer, None = publier maintenant
        platform_configs: Dict de configs par plateforme (captions custom, etc.)
    """
    body = {
        "caption": caption,
        "media": media_ids,
        "social_accounts": account_ids,
        "processing_enabled": True,
    }

    if scheduled_at:
        body["scheduled_at"] = scheduled_at

    if platform_configs:
        body["platform_configurations"] = platform_configs

    return _post("/posts", api_key, body)


def get_post_results(api_key, post_id=None):
    """Récupère les résultats de publication."""
    params = {"limit": 50}
    if post_id:
        params["post_id"] = [post_id]
    return _get("/post-results", api_key, params)


def get_post(api_key, post_id):
    """Récupère les détails d'un post."""
    return _get(f"/posts/{post_id}", api_key)
