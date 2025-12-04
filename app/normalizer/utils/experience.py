import re
from typing import List, Tuple

EXPERIENCE_TAG_TO_LEVEL = {
    "1-3 years": "junior",
    "3-5 years": "mid-level",
    "5+ years": "senior",
}

_EXPERIENCE_PATTERNS = (
    # allow optional trailing "experience" wording
    (
        r"^1\s*[-–]\s*3\s*(years?|yrs?)?(\s*(of\s*)?(experience|exp))?$",
        "junior",
    ),
    (
        r"^3\s*[-–]\s*5\s*(years?|yrs?)?(\s*(of\s*)?(experience|exp))?$",
        "mid-level",
    ),
    (
        r"^5\s*\+\s*(years?|yrs?)?(\s*(of\s*)?(experience|exp))?$",
        "senior",
    ),
)

_PRIORITY = {"junior": 1, "mid-level": 2, "senior": 3}


def _normalize_tag(tag: str) -> str:
    """Normalize a tag for comparison."""

    return tag.strip().lower()


def _get_experience_level(tag: str) -> str:
    """Return the mapped experience level for a single tag if present."""

    normalized = _normalize_tag(tag)

    level = EXPERIENCE_TAG_TO_LEVEL.get(normalized)
    if level:
        return level

    for pattern, mapped_level in _EXPERIENCE_PATTERNS:
        if re.match(pattern, normalized):
            return mapped_level

    return ""

def split_tags_and_experience(job_tags: List[str]) -> Tuple[List[str], str]:
    """
    Separate experience tags from the rest while deriving the experience level.

    Returns a tuple of (cleaned_tags, experience_level) where cleaned_tags
    excludes any experience-related tags (e.g. "1-3 years") and
    experience_level is the most senior mapped level.
    """
    if not job_tags:
        return [], ""

    cleaned: List[str] = []
    levels: List[str] = []

    for tag in job_tags:
        level = _get_experience_level(tag)
        if level:
            levels.append(level)
            continue

        trimmed = tag.strip()
        if trimmed:
            cleaned.append(trimmed)

    experience_level = max(levels, key=lambda l: _PRIORITY[l]) if levels else ""

    return cleaned, experience_level

def derive_experience_level(job_tags: List[str]) -> str:
    """
    Derive experience_level from tags BUT do NOT remove tags.
    If multiple exp tags exist, pick the most senior.
    """
    if not job_tags:
        return ""

    levels = []
    for t in job_tags:
        lvl = _get_experience_level(t)
        if lvl:
            levels.append(lvl)

    if not levels:
        return ""

    return max(levels, key=lambda l: _PRIORITY[l])
