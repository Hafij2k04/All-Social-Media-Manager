"""ডাটা সেভ/লোড। এখন JSON ফাইল (অস্থায়ী)। V2 তে শুধু এই ফাইলের ভেতরটা ডাটাবেস দিয়ে বদলাবে,
বাকি কোড অপরিবর্তিত থাকবে।"""
import json
import os

import config

_DEFAULT = {"accounts": {}, "ai_keys": {}, "active_ai": None}


def _load():
    if os.path.exists(config.DATA_FILE):
        try:
            with open(config.DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            for k, v in _DEFAULT.items():
                d.setdefault(k, type(v)() if v is not None else None)
            return d
        except Exception:
            pass
    return json.loads(json.dumps(_DEFAULT))


def _save(d):
    with open(config.DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


# ---- অ্যাকাউন্ট ও চ্যানেল ডেটা ----
def get_accounts():
    return _load()["accounts"]


def add_account(platform, name, data):
    """
    নতুন অ্যাকাউন্ট বা চ্যানেল সেভ করে।
    data যদি সাধারণ টেক্সট (লিংক) হয় অথবা ডিকশনারি (API Key, Channel ID সহ) হয়—দুটোই সাপোর্ট করবে।
    """
    d = _load()
    if isinstance(data, str):
        # পুরনো স্ট্রিং ফরম্যাট হলে ডিকশনারিতে রূপান্তর করে নেবে
        account_info = {
            "link": data,
            "channel_id": "",
            "api_key": "",
            "oauth_token": None,
            "stats": {}
        }
    elif isinstance(data, dict):
        account_info = data
    else:
        account_info = {"link": str(data)}

    d["accounts"].setdefault(platform, {})[name] = account_info
    _save(d)


def get_account_details(platform, name):
    """নির্দিষ্ট কোনো চ্যানেল বা আইডির সব তথ্য (API, স্ট্যাটাস ইত্যাদি) রিটার্ন করে।"""
    accs = get_accounts().get(platform, {})
    val = accs.get(name)
    if isinstance(val, str):
        return {
            "link": val,
            "channel_id": "",
            "api_key": "",
            "oauth_token": None,
            "stats": {}
        }
    return val or {}


def update_account_details(platform, name, updates: dict):
    """অ্যাকাউন্টের API Key, Token বা Analytics ডাটা আপডেট করার জন্য।"""
    d = _load()
    platform_accs = d["accounts"].setdefault(platform, {})
    current = platform_accs.get(name, {})
    if isinstance(current, str):
        current = {"link": current}
    current.update(updates)
    platform_accs[name] = current
    _save(d)


def remove_account(platform, name):
    """কোনো অ্যাকাউন্ট বা চ্যানেল ডিলিট করার জন্য।"""
    d = _load()
    if platform in d["accounts"] and name in d["accounts"][platform]:
        del d["accounts"][platform][name]
        _save(d)
        return True
    return False


# ---- AI ----
def get_ai_keys():
    return _load()["ai_keys"]


def set_ai_key(provider, key):
    d = _load()
    d["ai_keys"][provider] = key
    _save(d)


def get_active_ai():
    return _load()["active_ai"]


def set_active_ai(provider):
    d = _load()
    d["active_ai"] = provider
    _save(d)
