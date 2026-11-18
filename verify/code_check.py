import hashlib
import hmac
import secrets
import threading
import time
from enum import Enum


CODE_TTL_SECONDS = 300
MAX_VERIFY_ATTEMPTS = 5

_HASH_ITERATIONS = 100_000
_store_lock = threading.RLock()

code_store = dict()


class CodeVerificationStatus(str, Enum):
    OK = "ok"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    EXPIRED = "expired"
    ALREADY_USED = "already_used"
    TOO_MANY_ATTEMPTS = "too_many_attempts"
    INVALID_SESSION = "invalid_session"


def _hash_code(code: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        code.encode("utf-8"),
        salt,
        _HASH_ITERATIONS,
    ).hex()


def _matches(entry: dict, code: str) -> bool:
    stored_hash = entry.get("code")
    if not stored_hash:
        return False
    candidate = _hash_code(code, bytes.fromhex(entry["salt"]))
    return hmac.compare_digest(stored_hash, candidate)


def _new_entry(code: str, now: float) -> dict:
    salt = secrets.token_bytes(16)
    return {
        "code": _hash_code(code, salt),
        "salt": salt.hex(),
        "expires_at": now + CODE_TTL_SECONDS,
        "attempts": 0,
        "state": "active",
    }


def generate_sms_code(session_id: str):
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id must be a non-empty string")

    with _store_lock:
        previous = code_store.get(session_id)
        while True:
            code = f"{secrets.randbelow(1_000_000):06d}"
            if (
                previous is None
                or previous.get("state") != "active"
                or not _matches(previous, code)
            ):
                break

        code_store[session_id] = _new_entry(code, time.time())
    return code


def verify_code_result(session_id: str, input_code: str) -> CodeVerificationStatus:
    if not isinstance(session_id, str) or not session_id.strip():
        return CodeVerificationStatus.INVALID_SESSION

    with _store_lock:
        entry = code_store.get(session_id)
        if entry is None:
            return CodeVerificationStatus.NOT_FOUND

        state = entry.get("state")
        if state == "used":
            return CodeVerificationStatus.ALREADY_USED
        if state == "exhausted":
            return CodeVerificationStatus.TOO_MANY_ATTEMPTS

        if time.time() >= entry["expires_at"]:
            entry["state"] = "expired"
            entry["code"] = None
            entry["salt"] = None
            return CodeVerificationStatus.EXPIRED

        if isinstance(input_code, str) and _matches(entry, input_code):
            entry["state"] = "used"
            entry["code"] = None
            entry["salt"] = None
            entry["used_at"] = time.time()
            return CodeVerificationStatus.OK

        entry["attempts"] += 1
        if entry["attempts"] >= MAX_VERIFY_ATTEMPTS:
            entry["state"] = "exhausted"
            entry["code"] = None
            entry["salt"] = None
            return CodeVerificationStatus.TOO_MANY_ATTEMPTS
        return CodeVerificationStatus.INVALID


def verify_code(session_id: str, input_code: str) -> bool:
    return verify_code_result(session_id, input_code) is CodeVerificationStatus.OK
