"""
redis_cache.py
==============
Simple Redis helper for CV deduplication.

How it works:
  - CV text is hashed (sha256, first 1000 chars) → same function as _cv_fingerprint in runner.py
  - The hash is stored in Redis as a key with value = the candidate_id string
  - On upload: check Redis first. Hit → skip processing. Miss → process → store hash.

Key format : cv_hash:<hex_digest>
TTL        : None by default (hashes persist forever — a CV in DB stays cached)
             Set REDIS_CV_TTL_SECONDS in .env to expire after N seconds if you want.
"""

import os
import hashlib
import redis
from dotenv import load_dotenv

load_dotenv()

_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_TTL       = int(os.getenv("REDIS_CV_TTL_SECONDS", 0))   # 0 = no expiry

_client: redis.Redis | None = None


def _get_client() -> redis.Redis:
    """Lazy singleton Redis client."""
    global _client
    if _client is None:
        _client = redis.from_url(_REDIS_URL, decode_responses=True)
    return _client


def _hash_cv(text: str) -> str:
    """
    Produce the same fingerprint as runner._cv_fingerprint but as full 64-char hex
    so we can use it as a Redis key without collision risk.
    (runner._cv_fingerprint truncates to 12 chars for readability — fine for IDs,
     but we want the full digest for cache keys.)
    """
    sample = text[:1000].strip()
    return hashlib.sha256(sample.encode("utf-8", errors="replace")).hexdigest()


def _key(digest: str) -> str:
    return f"cv_hash:{digest}"


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def is_cached(cv_text: str) -> bool:
    """
    Return True if this CV text has already been processed and is in Redis.
    Safe to call even if Redis is down — returns False on any connection error
    so processing continues normally (fail-open).
    """
    try:
        digest = _hash_cv(cv_text)
        return _get_client().exists(_key(digest)) == 1
    except Exception as e:
        print(f"  ⚠️  Redis check failed (fail-open): {e}")
        return False


def get_cached_candidate_id(cv_text: str) -> str | None:
    """
    Return the candidate_id string stored for this CV hash, or None if not cached.
    """
    try:
        digest = _hash_cv(cv_text)
        return _get_client().get(_key(digest))
    except Exception as e:
        print(f"  ⚠️  Redis get failed: {e}")
        return None


def mark_as_cached(cv_text: str, candidate_id: str) -> None:
    """
    Store the CV hash → candidate_id mapping in Redis after successful DB storage.
    Respects REDIS_CV_TTL_SECONDS if set.
    """
    try:
        digest = _hash_cv(cv_text)
        client = _get_client()
        if _TTL > 0:
            client.setex(_key(digest), _TTL, candidate_id)
        else:
            client.set(_key(digest), candidate_id)
        print(f"  ✅ Redis: cached hash for candidate_id={candidate_id}")
    except Exception as e:
        print(f"  ⚠️  Redis set failed (non-fatal): {e}")


def invalidate(cv_text: str) -> None:
    """
    Remove a CV hash from Redis (e.g. if you want to force re-processing).
    """
    try:
        digest = _hash_cv(cv_text)
        _get_client().delete(_key(digest))
    except Exception as e:
        print(f"  ⚠️  Redis delete failed: {e}")


def ping() -> bool:
    """Health-check — returns True if Redis is reachable."""
    try:
        return _get_client().ping()
    except Exception:
        return False