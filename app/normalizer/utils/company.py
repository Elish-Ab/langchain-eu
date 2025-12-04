import re

def normalize_company_shape(name: str) -> str:
    n = (name or "").strip()
    if not n:
        return ""
    n = n.replace("-dot-", ".").replace(" dot ", ".").replace(" dot-", ".")
    return n[:1].upper() + n[1:]

def company_is_valid(name: str) -> bool:
    if not name:
        return False
    n = name.strip()
    if not n or len(n) > 100:
        return False
    if not re.search(r"[A-Za-z]", n):
        return False
    bad_endings = (" are", " is", " we", " hiring", " expanding", " growing", ":", ";")
    if any(n.lower().endswith(b) for b in bad_endings):
        return False
    return True
