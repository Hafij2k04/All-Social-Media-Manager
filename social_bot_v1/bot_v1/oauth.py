"""YouTube OAuth 2.0 helpers. Secrets are read only from environment variables."""
import json
import time
import urllib.parse
import urllib.request

import config


GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
]


def build_authorization_url(state: str) -> str:
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_REDIRECT_URI:
        raise RuntimeError("GOOGLE_CLIENT_ID and GOOGLE_REDIRECT_URI must be configured.")
    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(YOUTUBE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return GOOGLE_AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)


def exchange_authorization_code(code: str) -> dict:
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET or not config.GOOGLE_REDIRECT_URI:
        raise RuntimeError("Google OAuth environment variables are incomplete.")
    payload = urllib.parse.urlencode({
        "code": code,
        "client_id": config.GOOGLE_CLIENT_ID,
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode("utf-8")
    request = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not data.get("access_token"):
        raise RuntimeError("Google did not return an access token.")
    data["expires_at"] = int(time.time()) + int(data.get("expires_in", 3600))
    return data



def refresh_access_token(refresh_token: str) -> dict:
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
        raise RuntimeError("Google OAuth client credentials are not configured.")
    payload = urllib.parse.urlencode({
        "client_id": config.GOOGLE_CLIENT_ID,
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode("utf-8")
    request = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not data.get("access_token"):
        raise RuntimeError("Google did not return a refreshed access token.")
    data["expires_at"] = int(time.time()) + int(data.get("expires_in", 3600))
    return data


def get_valid_youtube_access_token(platform: str, account_name: str) -> str:
    credentials = __import__("storage").get_youtube_oauth(platform, account_name)
    access_token = credentials.get("access_token", "")
    expires_at = credentials.get("expires_at", 0)
    refresh_token = credentials.get("refresh_token", "")
    if not access_token:
        return ""
    if expires_at and expires_at <= int(time.time()) + 60 and refresh_token:
        refreshed = refresh_access_token(refresh_token)
        refreshed.setdefault("refresh_token", refresh_token)
        __import__("storage").save_youtube_oauth(platform, account_name, refreshed)
        access_token = refreshed["access_token"]
    return access_token



def fetch_authorized_youtube_channel(access_token: str) -> dict:
    """Return the channel belonging to the Google account that approved OAuth."""
    url = "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true"
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        data = json.loads(response.read().decode("utf-8"))
    items = data.get("items") or []
    if not items:
        raise RuntimeError("No YouTube channel was found for the authorized Google account.")
    item = items[0]
    snippet = item.get("snippet", {})
    return {
        "channel_id": item.get("id", ""),
        "channel_title": snippet.get("title", ""),
        "channel_custom_url": snippet.get("customUrl", ""),
    }


# ---- Meta / Facebook Login OAuth ----
META_SCOPES = ["pages_show_list", "pages_read_engagement"]


def build_facebook_authorization_url(state: str) -> str:
    if not config.META_APP_ID or not config.META_REDIRECT_URI:
        raise RuntimeError("META_APP_ID and META_REDIRECT_URI must be configured.")
    params = {
        "client_id": config.META_APP_ID,
        "redirect_uri": config.META_REDIRECT_URI,
        "response_type": "code",
        "scope": ",".join(META_SCOPES),
        "state": state,
    }
    base = f"https://www.facebook.com/{config.META_GRAPH_VERSION}/dialog/oauth"
    return base + "?" + urllib.parse.urlencode(params)


def _facebook_graph_get(path: str, params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"https://graph.facebook.com/{config.META_GRAPH_VERSION}/{path.lstrip('/')}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "All-Social-Media-Manager/1.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def exchange_facebook_authorization_code(code: str) -> dict:
    if not config.META_APP_ID or not config.META_APP_SECRET or not config.META_REDIRECT_URI:
        raise RuntimeError("Meta OAuth environment variables are incomplete.")
    short_lived = _facebook_graph_get("oauth/access_token", {
        "client_id": config.META_APP_ID,
        "client_secret": config.META_APP_SECRET,
        "redirect_uri": config.META_REDIRECT_URI,
        "code": code,
    })
    user_token = short_lived.get("access_token", "")
    if not user_token:
        raise RuntimeError("Meta did not return a user access token.")
    long_lived = _facebook_graph_get("oauth/access_token", {
        "grant_type": "fb_exchange_token",
        "client_id": config.META_APP_ID,
        "client_secret": config.META_APP_SECRET,
        "fb_exchange_token": user_token,
    })
    access_token = long_lived.get("access_token", user_token)
    expires_in = int(long_lived.get("expires_in", short_lived.get("expires_in", 0)) or 0)
    return {
        "user_access_token": access_token,
        "expires_at": int(time.time()) + expires_in if expires_in else 0,
        "token_type": "Bearer",
    }


def fetch_facebook_pages(user_access_token: str) -> list:
    """Return Pages the authorizing user can access, including each Page access token."""
    data = _facebook_graph_get("me/accounts", {
        "fields": "id,name,access_token,followers_count,fan_count,tasks",
        "limit": 100,
        "access_token": user_access_token,
    })
    return data.get("data") or []
