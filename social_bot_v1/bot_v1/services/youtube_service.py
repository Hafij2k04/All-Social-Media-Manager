import re
import urllib.parse
import urllib.error
import json
import urllib.request


def _format_num(val, unavailable: str = "Unavailable") -> str:
    # Missing API fields must not be silently converted to a misleading zero.
    if val is None or val == "":
        return unavailable
    try:
        return f"{int(val):,}"
    except (TypeError, ValueError):
        return unavailable


def extract_channel_identifier(link_or_id: str):
    """লিংক বা টেক্সট থেকে Channel ID (UC...) অথবা Handle (@...) বের করে।"""
    s = (link_or_id or "").strip()
    if not s:
        return None, None

    # সরাসরি Channel ID (UC দিয়ে শুরু ২৪ অক্ষরের আইডি)
    m_id = re.search(r"(UC[a-zA-Z0-9_-]{22})", s)
    if m_id:
        return "id", m_id.group(1)

    # হ্যান্ডেল (@handle)
    m_handle = re.search(r"@([a-zA-Z0-9_.-]+)", s)
    if m_handle:
        handle = m_handle.group(1).split("/")[0].split("?")[0]
        return "forHandle", "@" + handle

    # যদি শুধু চ্যানেলের ইউজারনেম বা কাস্টম নাম দেয় (লিংক ছাড়া)
    if not s.startswith("http") and " " not in s and len(s) > 2:
        return "forHandle", ("@" + s.lstrip("@"))

    return None, None


def fetch_youtube_stats(channel_id_or_link: str, api_key: str = "", access_token: str = ""):
    """Fetch channel statistics; OAuth uses the channel authorized by the signed-in Google account."""
    if not api_key and not access_token:
        return None, "⚠️ YouTube API Key অথবা Google OAuth connection প্রয়োজন। Account Dashboard থেকে Connect YouTube with Google চাপুন।"

    kind, val = extract_channel_identifier(channel_id_or_link)
    if not access_token and not kind:
        return None, "⚠️ সঠিক Channel ID (যেমন: UC...) অথবা হ্যান্ডেল (যেমন: @Clipzilla) পাওয়া যায়নি। '🆔 Set ID / Handle' বাটনে গিয়ে এটি সেট করুন।"

    # For OAuth, query the channel belonging to the Google account that granted consent.
    params = {"part": "snippet,statistics"}
    if access_token:
        params["mine"] = "true"
    else:
        params[kind] = val
        params["key"] = api_key.strip()
    url = "https://www.googleapis.com/youtube/v3/channels?" + urllib.parse.urlencode(params)

    try:
        headers = {"User-Agent": "All-Social-Media-Manager/1.0"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        items = data.get("items") or []
        if not items:
            target = "authorized Google account" if access_token else val
            return None, f"❌ {target} থেকে কোনো YouTube channel পাওয়া যায়নি। Google-এ সঠিক channel/account নির্বাচন করে আবার Connect করুন।"

        ch = next((item for item in items if item.get("id") == channel_id_or_link), items[0])
        snippet = ch.get("snippet") or {}
        stats = ch.get("statistics") or {}
        if not stats:
            return None, "❌ YouTube channel পাওয়া গেছে, কিন্তু API statistics দেয়নি। Google OAuth permission এবং YouTube Data API access যাচাই করতে হবে।"

        result = {
            "channel_id": ch.get("id", ""),
            "title": snippet.get("title", ""),
            "subscribers": _format_num(stats.get("subscriberCount"), "Hidden / Not public"),
            "views": _format_num(stats.get("viewCount")),
            "videos": _format_num(stats.get("videoCount")),
        }
        return result, None

    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
            api_error = err_body.get("error", {})
            msg = api_error.get("message", str(e))
            reason = (api_error.get("errors") or [{}])[0].get("reason", "")
            if reason:
                msg = f"{reason}: {msg}"
        except Exception:
            msg = str(e)
        return None, f"❌ YouTube API Error: {msg[:180]}"
    except Exception as e:
        return None, f"❌ সংযোগ ত্রুটি: {str(e)[:180]}"


def fetch_facebook_stats(page_id: str, access_token: str):
    """Facebook Graph API ব্যবহার করে পেজের ফলোয়ার এবং নাম নিয়ে আসে।"""
    if not access_token:
        return None, "⚠️ Page Access Token সেট করা নেই। প্রথমে '🔐 Set Access Token' বাটনে গিয়ে টোকেন দিন।"
    if not page_id or page_id == "লিংক নেই" or "facebook.com" in page_id:
        page_id = "me"

    params = {
        "fields": "id,name,followers_count,fan_count",
        "access_token": access_token.strip()
    }
    url = f"https://graph.facebook.com/v19.0/{urllib.parse.quote(page_id.strip())}?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        followers = data.get("followers_count") or data.get("fan_count") or 0
        likes = data.get("fan_count") or 0

        return {
            "channel_id": data.get("id", page_id),
            "title": data.get("name", ""),
            "subscribers": _format_num(followers),
            "views": f"{_format_num(likes)} (Likes)",
            "videos": "Sync Ready",
        }, None
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
            msg = err_body.get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)
        return None, f"❌ Facebook API Error: {msg[:120]}"
    except Exception as e:
        return None, f"❌ সংযোগ ত্রুটি: {str(e)[:120]}"
