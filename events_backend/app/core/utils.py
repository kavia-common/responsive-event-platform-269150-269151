from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from bson import ObjectId


def now_iso() -> str:
    """Current UTC timestamp in ISO8601 string."""
    return datetime.now(timezone.utc).isoformat()


def to_object_id(id_str: str) -> ObjectId:
    """Convert string to ObjectId with clear error."""
    try:
        return ObjectId(id_str)
    except Exception as exc:  # pragma: no cover
        raise ValueError("Invalid id") from exc


def clean_mongo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Mongo _id -> id and coerce ObjectId values to strings."""
    out: Dict[str, Any] = {}
    for k, v in doc.items():
        if k == "_id":
            out["id"] = str(v)
        elif isinstance(v, ObjectId):
            out[k] = str(v)
        else:
            out[k] = v
    return out
