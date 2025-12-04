from typing import List

EXPERIENCE_TAG_TO_LEVEL = {
    "1-3 years": "junior",
    "3-5 years": "mid-level",
    "5+ years": "senior",
}

_PRIORITY = {"junior": 1, "mid-level": 2, "senior": 3}

def derive_experience_level(job_tags: List[str]) -> str:
    """
    Derive experience_level from tags BUT do NOT remove tags.
    If multiple exp tags exist, pick the most senior.
    """
    if not job_tags:
        return ""

    levels = []
    for t in job_tags:
        lvl = EXPERIENCE_TAG_TO_LEVEL.get(t)
        if lvl:
            levels.append(lvl)

    if not levels:
        return ""

    return max(levels, key=lambda l: _PRIORITY[l])
