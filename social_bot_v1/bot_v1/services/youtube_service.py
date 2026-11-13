import re
import urllib.parse
import json
import urllib.request


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
        return "forHandle", "@" + m_handle.group(1)

    return None, None


def fetch_youtube_stats(channel_id_or_link: str, api_key: str):
    """YouTube Data API v3 ব্যবহার করে চ্যানেলের রিয়েল-টাইম স্ট্যাটাস নিয়ে আসে।"""
    if not api_key:
        return None, "⚠️ API Key সেট করা নেই। রিয়েল-টাইম ডেটা আনতে প্রথমে API Key যুক্ত করুন।"

    kind, val = extract_channel_identifier(channel_id_or_link)
    if not kind:
        return None, "⚠️ সঠিক Channel ID (যেমন: UC...) অথবা হ্যান্ডেল লিংক (যেমন: youtube.com/@channel) পাওয়া যায়নি।"

    params = {
        "part": "snippet,statistics",
        kind: val,
        "key": api_key.strip()
    }
    url = "https://www.googleapis.com/youtube/v3/channels?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        items = data.get("items", [])
        if not items:
            return None, "❌ এই Channel ID বা লিংকে কোনো YouTube চ্যানেল খুঁজে পাওয়া যায়নি।"

        ch = items[0]
        snippet = ch.get("snippet", {})
        stats = ch.get("statistics", {})

        result = {
            "channel_id": ch.get("id", ""),
            "title": snippet.get("title", ""),
            "subscribers": stats.get("subscriberCount", "0"),
            "views": stats.get("viewCount", "0"),
            "videos": stats.get("videoCount", "0"),
        }
        return result, None

    except Exception as e:
        return None, f"❌ API Error: {str(e)[:120]}"
