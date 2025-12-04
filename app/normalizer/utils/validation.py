from typing import Iterable, List, Any
from app.normalizer.utils.text import unique_keep_order

def validate_one(value: str, allowed: List[str]) -> str:
    return value if value in allowed else ""

def validate_many(values: Iterable[str], allowed: List[str]) -> List[str]:
    allowed_set = set(allowed)
    return [v for v in unique_keep_order(values or []) if v in allowed_set]

def coerce_list(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x]
    if isinstance(x, str) and x.strip():
        return [x.strip()]
    return []
