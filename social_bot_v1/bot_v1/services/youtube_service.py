import re
import urllib.parse
import urllib.error
import json
import urllib.request


def _format_num(val) -> str:
    try:
        return f"{int(val):,}"
    except Exception:
        return str(val or "0")


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
    """YouTube Data API v3 ব্যবহার করে চ্যানেলের রিয়েল-টাইম স্ট্যাটাস নিয়ে আসে।"""
    if not api_key and not access_token:
        return None, "⚠️ YouTube API Key অথবা Google OAuth connection প্রয়োজন। Account Dashboard থেকে Connect YouTube with Google চাপুন।"

    kind, val = extract_channel_identifier(channel_id_or_link)
    if not kind:
        return None, "⚠️ সঠিক Channel ID (যেমন: UC...) অথবা হ্যান্ডেল (যেমন: @Clipzilla) পাওয়া যায়নি। '🆔 Set ID / Handle' বাটনে গিয়ে এটি সেট করুন।"

    params = {
        "part": "snippet,statistics",
        kind: val,
    }
    if not access_token:
        params["key"] = api_key.strip()
    url = "https://www.googleapis.com/youtube/v3/channels?" + urllib.parse.urlencode(params)

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        items = data.get("items", [])
        if not items:
            return None, f"❌ `{val}` দিয়ে কোনো YouTube চ্যানেল খুঁজে পাওয়া যায়নি। সঠিক Channel ID বা @Handle দিন।"

        ch = items[0]
        snippet = ch.get("snippet", {})
        stats = ch.get("statistics", {})

        result = {
            "channel_id": ch.get("id", ""),
            "title": snippet.get("title", ""),
            "subscribers": _format_num(stats.get("subscriberCount", "0")),
            "views": _format_num(stats.get("viewCount", "0")),
            "videos": _format_num(stats.get("videoCount", "0")),
        }
        return result, None

    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
            msg = err_body.get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)
        return None, f"❌ YouTube API Error: {msg[:120]}"
    except Exception as e:
        return None, f"❌ সংযোগ ত্রুটি: {str(e)[:120]}"


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
