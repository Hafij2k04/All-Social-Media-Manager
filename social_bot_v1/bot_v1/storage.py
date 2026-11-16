"""ডাটা সেভ/লোড এবং Firestore persistent storage।"""
import json
import logging
import os
from threading import RLock

import config

log = logging.getLogger(__name__)

_DEFAULT = {
    "accounts": {},
    "ai_keys": {},
    "active_ai": None,
    "custom_platforms": [],
    "user_languages": {},
    "analysis_selections": {},
    "oauth_pending": {}
}

_firestore_client = None
_firestore_checked = False
_firestore_lock = RLock()
_firestore_document = None


def _normalize(data):
    if not isinstance(data, dict):
        data = {}
    for key, value in _DEFAULT.items():
        data.setdefault(key, type(value)() if value is not None else None)
    return data


def _get_firestore_document():
    """Initialize Firebase Admin lazily; local JSON remains available for local development."""
    global _firestore_client, _firestore_checked, _firestore_document
    with _firestore_lock:
        if _firestore_checked:
            return _firestore_document
        _firestore_checked = True
        service_account_path = getattr(
            config, "FIREBASE_SERVICE_ACCOUNT_FILE",
            "/etc/secrets/firebase-service-account.json"
        )
        if not os.path.isfile(service_account_path):
            log.warning(
                "Firebase service-account file not found at %s; using local JSON storage.",
                service_account_path
            )
            return None
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            try:
                firebase_admin.get_app()
            except ValueError:
                firebase_admin.initialize_app(
                    credentials.Certificate(service_account_path)
                )
            _firestore_client = firestore.client()
            _firestore_document = _firestore_client.collection("app_state").document("main")
            log.info("Firebase Firestore persistent storage initialized.")
            return _firestore_document
        except Exception:
            _firestore_checked = False
            log.exception("Firebase initialization failed; refusing silent local fallback.")
            raise


def _load_local():
    if os.path.exists(config.DATA_FILE):
        try:
            with open(config.DATA_FILE, "r", encoding="utf-8") as f:
                return _normalize(json.load(f))
        except Exception:
            log.exception("Could not read local data file.")
            raise

    env_backup = os.getenv("INITIAL_DATA_JSON", "").strip()
    if env_backup:
        return _normalize(json.loads(env_backup))
    return json.loads(json.dumps(_DEFAULT))


def _load():
    document = _get_firestore_document()
    if document is not None:
        snapshot = document.get()
        if snapshot.exists:
            data = (snapshot.to_dict() or {}).get("payload")
            if not isinstance(data, dict):
                raise RuntimeError("Firestore app_state/main document has no valid payload.")
            return _normalize(data)

        # First run: migrate existing Render/local JSON or INITIAL_DATA_JSON into Firestore.
        initial_data = _load_local()
        document.set({"payload": initial_data})
        log.info("Initial application data migrated to Firestore.")
        return initial_data

    return _load_local()


def _save(data):
    normalized = _normalize(data)
    document = _get_firestore_document()
    if document is not None:
        # Admin SDK writes server-side; Firestore client security rules do not grant public access.
        document.set({"payload": normalized})
        return

    with open(config.DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)


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



# ---- User language preference ----
def get_user_lang(user_id):
    """Return the saved language for a Telegram user; Bengali is the default."""
    return _load().get("user_languages", {}).get(str(user_id), "bn")


def set_user_lang(user_id, lang_code):
    """Save a user's selected language."""
    from lang import MESSAGES
    if lang_code not in MESSAGES:
        return False
    d = _load()
    d.setdefault("user_languages", {})[str(user_id)] = lang_code
    _save(d)
    return True


# ---- Analysis & Ideas: per-user multi-account selection ----
def get_analysis_selection(user_id):
    """Return the user's saved Analysis & Ideas account selection."""
    return _load().get("analysis_selections", {}).get(str(user_id), [])


def set_analysis_selection(user_id, targets):
    """Persist selected platform/account pairs for the Analysis & Ideas workflow."""
    clean = []
    seen = set()
    accounts = get_accounts()
    for item in targets:
        if not isinstance(item, dict):
            continue
        platform = str(item.get("platform", "")).strip()
        name = str(item.get("name", "")).strip()
        if not platform or not name or name not in accounts.get(platform, {}):
            continue
        key = (platform, name)
        if key in seen:
            continue
        seen.add(key)
        clean.append({"platform": platform, "name": name})

    d = _load()
    d.setdefault("analysis_selections", {})[str(user_id)] = clean
    _save(d)
    return clean



# ---- OAuth state and encrypted platform credentials ----
def _fernet():
    key = os.getenv("TOKEN_ENCRYPTION_KEY", "").strip()
    if not key:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY environment variable is required.")
    from cryptography.fernet import Fernet
    return Fernet(key.encode("utf-8"))


def _encrypt_secret(value):
    if not value:
        return ""
    return _fernet().encrypt(str(value).encode("utf-8")).decode("ascii")


def _decrypt_secret(value):
    if not value:
        return ""
    from cryptography.fernet import InvalidToken
    try:
        return _fernet().decrypt(str(value).encode("ascii")).decode("utf-8")
    except InvalidToken:
        raise RuntimeError("Stored OAuth credential cannot be decrypted. Check TOKEN_ENCRYPTION_KEY.")


def create_oauth_state(state, payload, expires_at):
    d = _load()
    d.setdefault("oauth_pending", {})[state] = {
        "payload": payload,
        "expires_at": int(expires_at),
    }
    _save(d)


def get_oauth_state(state):
    item = _load().get("oauth_pending", {}).get(state)
    if not item or int(item.get("expires_at", 0)) < int(__import__("time").time()):
        return None
    return item.get("payload")


def consume_oauth_state(state):
    d = _load()
    item = d.setdefault("oauth_pending", {}).pop(state, None)
    _save(d)
    if not item or int(item.get("expires_at", 0)) < int(__import__("time").time()):
        return None
    return item.get("payload")


def save_youtube_oauth(platform, name, token_data):
    d = _load()
    account = d.get("accounts", {}).get(platform, {}).get(name)
    if not isinstance(account, dict):
        raise KeyError("YouTube account not found.")
    account["oauth_access_token_encrypted"] = _encrypt_secret(token_data.get("access_token", ""))
    refresh = token_data.get("refresh_token")
    if refresh:
        account["oauth_refresh_token_encrypted"] = _encrypt_secret(refresh)
    account["oauth_expires_at"] = int(token_data.get("expires_at", 0))
    account["oauth_scope"] = token_data.get("scope", "")
    account["oauth_token_type"] = token_data.get("token_type", "Bearer")
    if token_data.get("channel_id"):
        account["channel_id"] = token_data["channel_id"]
        account["link"] = "https://www.youtube.com/channel/" + token_data["channel_id"]
    if token_data.get("channel_title"):
        account["channel_title"] = token_data["channel_title"]
    if token_data.get("channel_custom_url"):
        account["channel_custom_url"] = token_data["channel_custom_url"]
    account.pop("oauth_token", None)
    d["accounts"][platform][name] = account
    _save(d)


def get_youtube_oauth(platform, name):
    account = _load().get("accounts", {}).get(platform, {}).get(name, {})
    if not isinstance(account, dict):
        return {}
    access = account.get("oauth_access_token_encrypted", "")
    refresh = account.get("oauth_refresh_token_encrypted", "")
    # Backward compatibility for tokens manually entered before encrypted OAuth storage.
    legacy_access = account.get("oauth_token", "")
    return {
        "access_token": _decrypt_secret(access) if access else legacy_access,
        "refresh_token": _decrypt_secret(refresh) if refresh else "",
        "expires_at": int(account.get("oauth_expires_at", 0) or 0),
        "scope": account.get("oauth_scope", ""),
        "token_type": account.get("oauth_token_type", "Bearer"),
    }
