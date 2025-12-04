# app/normalizer/utils/experience.py
from typing import List, Tuple

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


def split_tags_and_experience(job_tags: List[str]) -> Tuple[List[str], str]:
    """
    Returns:
      cleaned_tags: tags with experience tags removed
      experience_level: derived level (junior/mid-level/senior or "")
    """
    exp_tags = set(EXPERIENCE_TAG_TO_LEVEL.keys())

    experience_level = derive_experience_level(job_tags)
    cleaned_tags = [t for t in job_tags if t not in exp_tags]

    return cleaned_tags, experience_level
