"""ডাটা সেভ/লোড এবং ব্যাকআপ রিকভারি সিস্টেম।"""
import json
import os
import config

_DEFAULT = {
    "accounts": {},
    "ai_keys": {},
    "active_ai": None,
    "custom_platforms": []
}


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

    # ফাইল না থাকলে Render-এর Environment Variable (INITIAL_DATA_JSON) থেকে রিকভার করার চেষ্টা করবে
    env_backup = os.getenv("INITIAL_DATA_JSON", "").strip()
    if env_backup:
        try:
            d = json.loads(env_backup)
            for k, v in _DEFAULT.items():
                d.setdefault(k, type(v)() if v is not None else None)
            _save(d)
            return d
        except Exception:
            pass

    return json.loads(json.dumps(_DEFAULT))


def _save(d):
    with open(config.DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def export_raw_json() -> str:
    """পুরো ডাটাবেস ব্যাকআপ নেওয়ার জন্য JSON স্ট্রিং রিটার্ন করে।"""
    return json.dumps(_load(), ensure_ascii=False)


# ---- প্ল্যাটফর্ম তালিকা ----
def get_all_platforms() -> list[str]:
    d = _load()
    base = list(getattr(config, "PLATFORMS", ["YouTube", "Facebook", "TikTok"]))
    for p in d.get("custom_platforms", []):
        if p not in base:
            base.append(p)
    return base


def add_custom_platform(platform_name: str):
    d = _load()
    customs = d.setdefault("custom_platforms", [])
    if platform_name not in customs and platform_name not in getattr(config, "PLATFORMS", []):
        customs.append(platform_name)
        _save(d)


# ---- অ্যাকাউন্ট ও চ্যানেল ডেটা ----
def get_accounts():
    return _load()["accounts"]


def add_account(platform, name, data):
    d = _load()
    if isinstance(data, str):
        account_info = {
            "link": data,
            "channel_id": "",
            "api_key": "",
            "oauth_token": None,
            "stats": {"subscribers": "0", "views": "0", "videos": "0"}
        }
    elif isinstance(data, dict):
        account_info = data
    else:
        account_info = {"link": str(data)}

    d["accounts"].setdefault(platform, {})[name] = account_info
    _save(d)


def get_account_details(platform, name):
    accs = get_accounts().get(platform, {})
    val = accs.get(name)
    if isinstance(val, str):
        return {
            "link": val,
            "channel_id": "",
            "api_key": "",
            "oauth_token": None,
            "stats": {"subscribers": "0", "views": "0", "videos": "0"}
        }
    return val or {}


def update_account_details(platform, name, updates: dict):
    d = _load()
    platform_accs = d["accounts"].setdefault(platform, {})
    current = platform_accs.get(name, {})
    if isinstance(current, str):
        current = {"link": current}
    current.update(updates)
    platform_accs[name] = current
    _save(d)


def remove_account(platform, name):
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
