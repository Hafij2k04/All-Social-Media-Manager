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


# ---- অ্যাকাউন্ট ----
def get_accounts():
    return _load()["accounts"]


def add_account(platform, name, link):
    d = _load()
    d["accounts"].setdefault(platform, {})[name] = link
    _save(d)


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
