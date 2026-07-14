"""
Storage — saves ANONYMIZED assessment records for the admin dashboard.

Privacy rules (non-negotiable):
  • Saved ONLY when the user explicitly consents ("রিপোর্ট সংরক্ষণ করতে চান?" → হ্যাঁ)
  • NO name, phone, address, or free-text detail is ever stored
  • Only aggregate analytics fields: abuse types, risk, district, division,
    gender, reporter type, abuser relation, ongoing, timestamp

Two backends, chosen automatically:
  1. Firestore  — if backend/firebase-key.json (service account) exists
  2. Local JSON — fallback for development/testing (backend/local_reports.json)

The local fallback means the whole flow can be built and tested before Firebase
is set up; adding the key later switches to Firestore with no code change.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND_DIR   = Path(__file__).parent.parent
FIREBASE_KEY  = BACKEND_DIR / "firebase-key.json"
LOCAL_STORE   = BACKEND_DIR / "local_reports.json"
COLLECTION    = "assessments"

# Fields that are allowed to leave the device. Anything not in this list is dropped.
ALLOWED_FIELDS = {
    "abuse_types", "risk_level", "severity", "district", "division",
    "gender", "reporter_type", "abuser_relation", "abuser_is_family", "ongoing",
}


class StorageError(Exception):
    pass


class ConsentRequiredError(StorageError):
    """Attempted to save without the user's consent."""


# ── Firestore (lazy) ──────────────────────────────────────────────────────────
_db = None
_backend: str | None = None


def _init() -> str:
    """Initialise the storage backend once. Returns 'firestore' or 'local'."""
    global _db, _backend
    if _backend:
        return _backend

    if FIREBASE_KEY.exists():
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                cred = credentials.Certificate(str(FIREBASE_KEY))
                firebase_admin.initialize_app(cred)
            _db = firestore.client()
            _backend = "firestore"
            return _backend
        except Exception as e:  # bad key, no network, etc. → fall back
            print(f"[storage] Firestore init failed ({e}); using local store.")

    _backend = "local"
    return _backend


def backend_name() -> str:
    return _init()


# ── Sanitiser ─────────────────────────────────────────────────────────────────
def sanitize(record: dict[str, Any]) -> dict[str, Any]:
    """Keep ONLY allowed analytics fields. Drops anything identifying."""
    return {k: v for k, v in record.items() if k in ALLOWED_FIELDS}


# ── Save ──────────────────────────────────────────────────────────────────────
def save_assessment(record: dict[str, Any], consent: bool) -> dict[str, Any]:
    """
    Save an anonymized assessment. Raises ConsentRequiredError without consent.

    Returns {"saved": True, "id": "...", "backend": "firestore"|"local"}
    """
    if not consent:
        raise ConsentRequiredError(
            "User did not consent to saving — nothing was stored."
        )

    doc = sanitize(record)
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    doc_id = uuid.uuid4().hex[:16]

    backend = _init()
    if backend == "firestore":
        try:
            _db.collection(COLLECTION).document(doc_id).set(doc)
        except Exception as e:
            raise StorageError(f"Firestore write failed: {e}") from e
    else:
        rows = _read_local()
        rows.append({"id": doc_id, **doc})
        LOCAL_STORE.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return {"saved": True, "id": doc_id, "backend": backend}


def _read_local() -> list[dict[str, Any]]:
    if not LOCAL_STORE.exists():
        return []
    try:
        return json.loads(LOCAL_STORE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


# ── Read (for the dashboard) ──────────────────────────────────────────────────
def fetch_all(limit: int = 5000) -> list[dict[str, Any]]:
    backend = _init()
    if backend == "firestore":
        try:
            docs = _db.collection(COLLECTION).limit(limit).stream()
            return [{"id": d.id, **d.to_dict()} for d in docs]
        except Exception as e:
            raise StorageError(f"Firestore read failed: {e}") from e
    return _read_local()[:limit]


def dashboard_stats() -> dict[str, Any]:
    """
    Aggregates for the six live dashboard charts:
    abuse type, monthly trend, gender, district, family vs non-family, risk.
    """
    rows = fetch_all()

    abuse_type:  dict[str, int] = {}
    gender:      dict[str, int] = {}
    district:    dict[str, int] = {}
    risk:        dict[str, int] = {}
    monthly:     dict[str, int] = {}
    family_split = {"family": 0, "non_family": 0}

    for row in rows:
        for t in row.get("abuse_types") or []:
            abuse_type[t] = abuse_type.get(t, 0) + 1

        g = row.get("gender") or "unknown"
        gender[g] = gender.get(g, 0) + 1

        d = row.get("district")
        if d:
            district[d] = district.get(d, 0) + 1

        r = str(row.get("risk_level") or "")
        if r:
            risk[r] = risk.get(r, 0) + 1

        if row.get("abuser_is_family") is True:
            family_split["family"] += 1
        elif row.get("abuser_is_family") is False:
            family_split["non_family"] += 1

        ts = row.get("created_at") or ""
        if len(ts) >= 7:
            month = ts[:7]  # YYYY-MM
            monthly[month] = monthly.get(month, 0) + 1

    return {
        "total_assessments": len(rows),
        "abuse_type":        abuse_type,
        "gender":            gender,
        "district":          district,
        "risk_level":        risk,
        "family_vs_non":     family_split,
        "monthly_trend":     dict(sorted(monthly.items())),
        "backend":           backend_name(),
    }


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    print(f"Backend: {backend_name()}")
    if backend_name() == "local":
        print(f"  (firebase-key.json নেই → local file: {LOCAL_STORE.name})")

    # Consent refused → nothing saved
    try:
        save_assessment({"abuse_types": ["physical"]}, consent=False)
    except ConsentRequiredError as e:
        print(f"\n✔ সম্মতি ছাড়া save হয়নি: {e}")

    # Identifying fields must be stripped
    dirty = {
        "abuse_types": ["physical", "neglect"], "risk_level": 4, "severity": 4,
        "district": "ময়মনসিংহ", "division": "ময়মনসিংহ", "gender": "female",
        "reporter_type": "self", "abuser_relation": "son",
        "abuser_is_family": True, "ongoing": True,
        # these MUST be dropped:
        "victim_name": "রাবেয়া বেগম", "phone": "01712345678",
        "extra_detail": "আমার ছেলে মারধর করেছে",
    }
    clean = sanitize(dirty)
    dropped = set(dirty) - set(clean)
    print(f"\n✔ বাদ দেওয়া হলো (পরিচয়): {sorted(dropped)}")

    res = save_assessment(dirty, consent=True)
    print(f"✔ সংরক্ষিত: {res}")

    print("\n=== Dashboard stats ===")
    for k, v in dashboard_stats().items():
        print(f"  {k:<18}: {v}")
