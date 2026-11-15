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
