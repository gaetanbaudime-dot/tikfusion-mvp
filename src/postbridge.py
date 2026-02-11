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

PLATFORM_COLORS = {
    "tiktok": "#FF004F",
    "instagram": "#E1306C",
    "youtube": "#FF0000",
    "facebook": "#1877F2",
    "twitter": "#1DA1F2",
    "linkedin": "#0A66C2",
    "pinterest": "#E60023",
    "threads": "#000000",
    "bluesky": "#0085FF",
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


def _patch(endpoint, api_key, json_data=None):
    r = requests.patch(f"{BASE_URL}{endpoint}", headers=_headers(api_key), json=json_data or {}, timeout=30)
    r.raise_for_status()
    return r.json()


def _delete(endpoint, api_key):
    r = requests.delete(f"{BASE_URL}{endpoint}", headers=_headers(api_key), timeout=15)
    r.raise_for_status()
    return r.json()


# ---------- Safe wrappers (return (data, error_str)) ----------

def safe_call(func, *args, **kwargs):
    """Wrap any API call — returns (result, None) or (None, error_string)."""
    try:
        return func(*args, **kwargs), None
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        body = ""
        try:
            body = e.response.json()
        except Exception:
            body = e.response.text[:300] if e.response is not None else str(e)
        return None, f"HTTP {status}: {body}"
    except requests.exceptions.ConnectionError:
        return None, "Connexion impossible — verifiez votre connexion internet"
    except requests.exceptions.Timeout:
        return None, "Timeout — le serveur PostBridge ne repond pas"
    except Exception as e:
        return None, str(e)


# ---------- Social Accounts ----------

def list_accounts(api_key):
    """Recupere tous les comptes sociaux connectes."""
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


def get_account(api_key, account_id):
    """Recupere un compte social par ID."""
    return _get(f"/social-accounts/{account_id}", api_key)


def get_account_fields(api_key):
    """Debug: retourne les champs du premier compte pour inspection."""
    data = _get("/social-accounts", api_key, {"offset": 0, "limit": 1})
    items = data.get("data", [])
    if items:
        return items[0]
    return {}


# ---------- Media ----------

def upload_video(api_key, video_path):
    """Upload une video via signed URL. Retourne le media_id."""
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


def list_media(api_key, post_id=None, media_type=None):
    """Liste les medias uploades."""
    params = {"limit": 50}
    if post_id:
        params["post_id"] = post_id if isinstance(post_id, list) else [post_id]
    if media_type:
        params["type"] = media_type if isinstance(media_type, list) else [media_type]
    return _get("/media", api_key, params)


def get_media(api_key, media_id):
    """Recupere un media par ID."""
    return _get(f"/media/{media_id}", api_key)


def delete_media(api_key, media_id):
    """Supprime un media."""
    return _delete(f"/media/{media_id}", api_key)


# ---------- Posts ----------

def create_post(api_key, caption, media_ids, account_ids,
                scheduled_at=None, platform_configs=None):
    """Cree un post (publication immediate ou programmee).

    Args:
        api_key: PostBridge API key
        caption: Texte principal du post
        media_ids: Liste de media_id (videos uploadees)
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


def list_posts(api_key, platform=None, status=None):
    """Liste les posts avec filtres optionnels."""
    params = {"limit": 50}
    if platform:
        params["platform"] = platform if isinstance(platform, list) else [platform]
    if status:
        params["status"] = status if isinstance(status, list) else [status]
    return _get("/posts", api_key, params)


def get_post(api_key, post_id):
    """Recupere les details d'un post."""
    return _get(f"/posts/{post_id}", api_key)


def update_post(api_key, post_id, caption=None, scheduled_at=None,
                media_ids=None, account_ids=None, platform_configs=None):
    """Met a jour un post existant (PATCH). Inclure scheduled_at pour les posts programmes."""
    body = {}
    if caption is not None:
        body["caption"] = caption
    if scheduled_at is not None:
        body["scheduled_at"] = scheduled_at
    if media_ids is not None:
        body["media"] = media_ids
    if account_ids is not None:
        body["social_accounts"] = account_ids
    if platform_configs is not None:
        body["platform_configurations"] = platform_configs
    return _patch(f"/posts/{post_id}", api_key, body)


def delete_post(api_key, post_id):
    """Supprime un post."""
    return _delete(f"/posts/{post_id}", api_key)


# ---------- Post Results ----------

def get_post_results(api_key, post_id=None):
    """Recupere les resultats de publication."""
    params = {"limit": 50}
    if post_id:
        params["post_id"] = [post_id] if isinstance(post_id, str) else post_id
    return _get("/post-results", api_key, params)


def get_post_result(api_key, result_id):
    """Recupere un resultat specifique."""
    return _get(f"/post-results/{result_id}", api_key)
